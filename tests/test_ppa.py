import csv
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ppa import assess_ppa, find_yosys, write_summary_ppa_csv

INVERTER = 'module TopModule(input a, output y); assign y=~a; endmodule'


class PpaFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rtl = self.root / 'final.sv'
        self.rtl.write_text(INVERTER, encoding='utf-8')

    def run_assessment(self, **options):
        return assess_ppa([self.rtl], self.root / 'ppa', functional_passed=True, **options)

    def test_missing_tool_keeps_functional_pass_and_unknown_metrics(self):
        report = self.run_assessment(yosys=str(self.root / 'missing.exe'))
        self.assertEqual(report['status'], 'tool_unavailable')
        self.assertTrue(report['functional_passed'])
        self.assertIsNone(report['synthesis_passed'])
        self.assertIsNone(report['area']['cell_count'])
        self.assertIsNone(report['power']['total_power_mw'])
        self.assertEqual(report['sources'][0]['sha256'], hashlib.sha256(self.rtl.read_bytes()).hexdigest())
        self.assertEqual(json.loads((self.root / 'ppa/report.json').read_text()), report)

    def test_nonzero_exit_cannot_be_reported_as_success(self):
        with patch('ppa.find_yosys', return_value='yosys'), patch('ppa.subprocess.run',
                return_value=SimpleNamespace(returncode=1, stdout='Yosys test\n', stderr='ERROR')):
            report = self.run_assessment()
        self.assertEqual(report['status'], 'synthesis_failed')
        self.assertFalse(report['synthesis_passed'])
        self.assertTrue(report['functional_passed'])
        self.assertIsNone(report['timing']['logic_depth'])

    def test_timeout_preserves_partial_log_and_unknown_synthesis(self):
        with patch('ppa.find_yosys', return_value='yosys'), patch('ppa.subprocess.run',
                side_effect=subprocess.TimeoutExpired('yosys', 1, output=b'partial', stderr=b'timed out')):
            report = self.run_assessment(timeout=1)
        self.assertEqual(report['status'], 'tool_timeout')
        self.assertIsNone(report['synthesis_passed'])
        self.assertIn('partial', (self.root / 'ppa/synthesis.log').read_text())

    def test_zero_exit_without_reports_is_not_a_pass(self):
        with patch('ppa.find_yosys', return_value='yosys'), patch('ppa.subprocess.run',
                return_value=SimpleNamespace(returncode=0, stdout='', stderr='')):
            report = self.run_assessment()
        self.assertNotEqual(report['status'], 'ok')
        self.assertIsNone(report['area']['cell_count'])

    def test_disabled_and_skipped_never_invoke_synthesis(self):
        with patch('ppa.subprocess.run') as process:
            report = self.run_assessment(mode='off')
            skipped = assess_ppa([], self.root / 'skipped')
        process.assert_not_called()
        self.assertEqual(report['status'], 'disabled')
        self.assertEqual(skipped['status'], 'skipped')

    def test_existing_output_cannot_reuse_stale_metrics(self):
        self.run_assessment(mode='off')
        with self.assertRaises(FileExistsError):
            self.run_assessment()

    def test_script_injection_in_top_is_rejected(self):
        with patch('ppa.subprocess.run') as process:
            report = self.run_assessment(top='TopModule; shell echo injected')
        process.assert_not_called()
        self.assertNotEqual(report['status'], 'ok')

    def test_csv_keeps_unavailable_numbers_blank_and_supports_direct_arms(self):
        report = self.run_assessment(mode='off')
        csv_path = self.root / 'ppa_results.csv'
        write_summary_ppa_csv(csv_path, [{'case_id': 'test', 'direct': {'ppa': report}}])
        with csv_path.open(encoding='utf-8-sig', newline='') as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row['variant'], 'direct')
        self.assertEqual(row['generic_cells'], '')
        self.assertEqual(row['total_power_mw'], '')

    def test_json_main_preserves_pass_when_ppa_tool_is_missing(self):
        import run_json_pipeline as runner
        dataset = self.root / 'dataset'
        dataset.mkdir()
        spec = dataset / 'test_prompt.txt'
        spec.write_text('Output is the complement of input.')
        output = self.root / 'experiment'

        def generated(case_id, spec_path, directory, *args, **kwargs):
            case_dir = directory / case_id
            case_dir.mkdir()
            (case_dir / 'final.sv').write_text(INVERTER)
            return {'case_id': case_id, 'passed': True, 'status': 'pass', 'iterations': []}

        with patch.object(sys, 'argv', ['run_json_pipeline.py', '--dataset', str(dataset),
                                       '--cases', 'test', '--output', str(output)]), \
             patch.object(runner.importlib.util, 'find_spec', return_value=object()), \
             patch.object(runner, 'environment_check', return_value={'passed': True}), \
             patch.object(runner, 'run_case', side_effect=generated), \
             patch('ppa.find_yosys', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(), 0)
        summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['passed'], 1)
        self.assertEqual(summary['results'][0]['status'], 'pass')
        self.assertEqual(summary['results'][0]['ppa']['status'], 'tool_unavailable')
        self.assertTrue((output / 'test/ppa/report.json').is_file())
        self.assertTrue((output / 'ppa_results.csv').is_file())


@unittest.skipUnless(find_yosys(), 'Yosys/YoWASP is not installed')
class PpaRealSynthesisTests(unittest.TestCase):
    def synthesize(self, source, *, top='TopModule', helper=None):
        with tempfile.TemporaryDirectory(prefix='ppa_中文_') as temporary:
            root = Path(temporary)
            rtl = root / 'final design.sv'
            rtl.write_text(source, encoding='utf-8-sig')
            paths = [rtl]
            if helper:
                helper_path = root / 'helper.sv'
                helper_path.write_text(helper)
                paths.append(helper_path)
            return assess_ppa(paths, root / 'report with spaces', top=top)

    def test_inverter_has_one_gate_and_one_level(self):
        report = self.synthesize(INVERTER)
        self.assertEqual(report['status'], 'ok', report)
        self.assertEqual(report['area']['cell_count'], 1)
        self.assertEqual(report['area']['flip_flop_cells'], 0)
        self.assertEqual(report['timing']['logic_depth'], 1)
        self.assertIsNone(report['timing']['critical_path_ns'])
        self.assertIsNone(report['power']['total_power_mw'])

    def test_sequential_boundary_and_flip_flop_count(self):
        report = self.synthesize('module TopModule(input clk,input [3:0] d,output reg [3:0] q);'
                                 'always @(posedge clk) q<=d; endmodule')
        self.assertEqual(report['status'], 'ok', report)
        self.assertEqual(report['area']['flip_flop_cells'], 4)
        self.assertEqual(report['timing']['logic_depth'], 0)

    def test_constant_output_zero_cells_is_valid(self):
        report = self.synthesize("module TopModule(output y); assign y=1'b0; endmodule")
        self.assertEqual(report['status'], 'ok', report)
        self.assertEqual(report['area']['cell_count'], 0)
        self.assertEqual(report['timing']['logic_depth'], 0)

    def test_helper_hierarchy_is_flattened_and_auto_top_is_recorded(self):
        report = self.synthesize('module chip(input a,output y); helper h(a,y); endmodule',
                                 top=None, helper='module helper(input a,output y); assign y=~a; endmodule')
        self.assertEqual(report['status'], 'ok', report)
        self.assertEqual(report['resolved_top'], 'chip')
        self.assertEqual(report['area']['cell_count'], 1)

    def test_broken_rtl_and_unresolved_cell_do_not_pass(self):
        for source in ['module TopModule(input a,output y);assign y=;endmodule',
                       'module TopModule(input a,output y); missing m(a,y);endmodule']:
            with self.subTest(source=source):
                report = self.synthesize(source)
                self.assertEqual(report['status'], 'synthesis_failed', report)
                self.assertIsNone(report['area']['cell_count'])


if __name__ == '__main__':
    unittest.main()
