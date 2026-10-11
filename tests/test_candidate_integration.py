import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import run_three_candidate_select as runner
from candidate_verification import select_with_generated_contract
from candidate_runtime import DEFAULT_DATASET, DEFAULT_IVERILOG, DEFAULT_VVP
from spec_directed_validator import build_testbench, run_contract
from test_json_pipeline import contract, SPEC

ROOT = Path(__file__).resolve().parents[1]
GOOD = 'module TopModule(input a,output q);assign q=~a;endmodule'
BAD = 'module TopModule(input a,output q);assign q=a;endmodule'
META = {'usage': {'total_tokens': 10}}


class CandidateIntegrationTests(unittest.TestCase):
    def test_all_imported_contracts_compile_to_testbench(self):
        contracts = list((ROOT / 'verification_contracts').glob('*.json'))
        self.assertEqual(len(contracts), 13)
        for path in contracts:
            with self.subTest(path=path.name):
                self.assertIn('DIRECTED_SUMMARY', build_testbench(json.loads(path.read_text(encoding='utf-8'))))

    def test_saved_contract_rejects_self_oracle_and_no_checks(self):
        value = json.loads((ROOT / 'verification_contracts/Prob005_notgate.json').read_text(encoding="utf-8"))
        bad = copy.deepcopy(value)
        bad['tests'][0]['steps'][0]['expect']['out'] = 'out'
        with self.assertRaises(ValueError):
            build_testbench(bad)
        value['tests'][0]['steps'][0].pop('expect')
        with self.assertRaises(ValueError):
            build_testbench(value)

    def test_saved_contract_real_simulation_rejects_wrong_rtl(self):
        with tempfile.TemporaryDirectory(prefix='候选_') as tmp:
            root = Path(tmp)
            module = root / 'module.sv'
            path = ROOT / 'verification_contracts/Prob005_notgate.json'
            for expr, expected in [('~in', True), ('in', False)]:
                module.write_text(f'module TopModule(input in,output out);assign out={expr};endmodule')
                result = run_contract(path, root, root / str(expected), str(DEFAULT_IVERILOG), str(DEFAULT_VVP), 'TopModule', module)
                self.assertEqual(result['passed'], expected, result)

    def test_generated_contract_selects_correct_candidate_without_reference(self):
        with tempfile.TemporaryDirectory(prefix='候选_') as tmp:
            root = Path(tmp)
            candidates = []
            for index, source in enumerate([BAD, GOOD], 1):
                directory = root / str(index)
                directory.mkdir()
                module = directory / 'module.sv'
                module.write_text(source)
                candidates.append({'candidate_id': index, 'final_syntax_pass': True, 'module_path': str(module)})
            def response(args, system, user):
                self.assertNotIn('assign q=', user)
                self.assertNotIn('_ref.sv', user)
                return json.dumps(contract()), META
            with patch('candidate_verification.call_api', side_effect=response):
                result = select_with_generated_contract(SimpleNamespace(), 'test', root, SPEC, candidates)
            self.assertEqual(result['selected_id'], 2)
            self.assertEqual(result['passing_candidate_ids'], [2])
            self.assertTrue((root / 'frozen_contract.json').is_file())

    def test_end_to_end_freezes_selection_before_official_evaluation(self):
        with tempfile.TemporaryDirectory(prefix='候选_') as tmp:
            root = Path(tmp)
            dataset = root / 'dataset'
            dataset.mkdir()
            (dataset / 'test_prompt.txt').write_text(SPEC)
            output = root / 'results'
            args = SimpleNamespace(dataset=dataset, output=output, model='mock', reasoning_effort='none',
                                   temperature=0, max_tokens=8192, max_repairs=0, case=['test'], limit=None,
                                   selection='contract', contract_dir=None, skip_official=False)
            responses = iter([BAD, GOOD, BAD])
            def official(case_id, module, test, ref, directory):
                frozen = json.loads((output / 'test/frozen_selection.json').read_text(encoding="utf-8"))
                self.assertEqual(frozen['selected_id'], 2)
                return {'pass': '~a' in module.read_text(), 'status': 'mock_official'}
            with patch.object(runner, 'parse_args', return_value=args), \
                 patch.object(runner, 'call_api', side_effect=lambda *a: (next(responses), META)), \
                 patch('candidate_verification.call_api', return_value=(json.dumps(contract()), META)), \
                 patch.object(runner, 'official_eval', side_effect=official):
                self.assertEqual(runner.main(), 0)
            summary = json.loads((output / 'summary.json').read_text(encoding="utf-8"))
            self.assertEqual(summary['metrics']['oracle_pass_at_3_count'], 1)
            self.assertEqual(summary['metrics']['pass_at_1_count'], 0)
            self.assertEqual(summary['metrics']['blind_select_at_3_count'], 1)
            self.assertTrue((output / 'test/selected.sv').is_file())
            self.assertTrue((output / 'results.csv').is_file())

    def test_official_failure_and_zero_samples_never_pass(self):
        from run_spec_card_ab import official_eval
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'official_sim.vvp').touch()
            for rc, samples in [(1, 10), (0, 0)]:
                with patch('run_spec_card_ab.run_process', side_effect=[(0, '', '', False), (rc, f'Mismatches: 0 in {samples} samples', '', False)]):
                    self.assertFalse(official_eval('test', root/'dut', root/'tb', root/'ref', root)['pass'])

    def test_real_official_evaluation_uses_existing_dataset(self):
        from run_spec_card_ab import official_eval
        with tempfile.TemporaryDirectory(prefix='官方_') as tmp:
            root = Path(tmp)
            module = root / 'module.sv'
            for expr, expected in [('~in', True), ('in', False)]:
                module.write_text(f'module TopModule(input in,output out);assign out={expr};endmodule')
                result = official_eval('Prob005_notgate', module,
                    DEFAULT_DATASET / 'Prob005_notgate_test.sv', DEFAULT_DATASET / 'Prob005_notgate_ref.sv', root)
                self.assertEqual(result['pass'], expected, result)

    def test_batch_error_circuit_breaker_preserves_unattempted_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / 'dataset'
            dataset.mkdir()
            for index in range(4):
                (dataset / f'Prob{index:03d}_example_prompt.txt').write_text(SPEC)
            output = root / 'results'
            args = SimpleNamespace(dataset=dataset, output=output, model='mock', reasoning_effort='none',
                                   temperature=0, max_tokens=8192, max_repairs=0, case=[], limit=None,
                                   selection='contract', contract_dir=None, skip_official=True)
            with patch.object(runner, 'parse_args', return_value=args), \
                 patch.object(runner, 'call_api', side_effect=RuntimeError('simulated API outage')), \
                 patch.object(runner, 'official_eval', side_effect=AssertionError('must not read official files')):
                self.assertEqual(runner.main(), 1)
            summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['completed_cases'], 3)
            self.assertEqual(summary['not_attempted'], ['Prob003_example'])
            self.assertIsNone(summary['metrics']['pass_at_1_rate'])


if __name__ == '__main__':
    unittest.main()
