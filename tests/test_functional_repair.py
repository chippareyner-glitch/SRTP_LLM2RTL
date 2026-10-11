import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from candidate_repair import repair_candidates
from candidate_runtime import DEFAULT_IVERILOG, DEFAULT_VVP, call_api
from rtl_json_pipeline.validation import validate
from test_json_pipeline import contract, SPEC

GOOD = 'module TopModule(input a,output q);assign q=~a;endmodule'
BAD = 'module TopModule(input a,output q);assign q=a;endmodule'


class FunctionalRepairTests(unittest.TestCase):
    def prepare(self, root, sources):
        frozen = root / 'frozen_contract.json'
        frozen.write_text(json.dumps(contract()), encoding='utf-8')
        candidates = []
        for index, source in enumerate(sources, 1):
            directory = root / str(index)
            directory.mkdir()
            module = directory / 'module_final.sv'
            module.write_text(source, encoding='utf-8')
            candidates.append({'candidate_id': index, 'module_path': str(module), 'final_syntax_pass': True,
                               'api_calls': 0, 'total_tokens': 0,
                               'directed': validate(source, contract(), directory / 'initial_check', DEFAULT_IVERILOG, DEFAULT_VVP)})
        return candidates

    def test_functional_failure_really_iterates_and_keeps_frozen_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self.prepare(root, [BAD, GOOD])
            before = (root / 'frozen_contract.json').read_bytes()
            def response(args, system, user):
                self.assertNotIn('official', user)
                self.assertNotIn('_ref.sv', user)
                self.assertIn('expected', user)
                return GOOD, {'usage': {'total_tokens': 15}}
            with patch('candidate_repair.call_api', side_effect=response) as mocked:
                repair_candidates(SimpleNamespace(max_functional_repairs=3), root, SPEC, contract(), rows)
            self.assertEqual(mocked.call_count, 1)
            self.assertTrue(rows[0]['directed']['passed'])
            self.assertEqual(rows[0]['functional_repairs'], 1)
            self.assertEqual(rows[1]['functional_repairs'], 0)
            self.assertEqual((root / 'frozen_contract.json').read_bytes(), before)
            self.assertTrue((root / '1/functional_repair_001/result.json').exists())

    def test_shared_failure_stops_without_blindly_repairing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self.prepare(root, [BAD, BAD, BAD])
            with patch('candidate_repair.call_api', side_effect=AssertionError('must not call API')):
                result = repair_candidates(SimpleNamespace(max_functional_repairs=3), root, SPEC, contract(), rows)
            self.assertEqual(result['status'], 'verifier_suspect')
            self.assertFalse(rows[0]['directed']['passed'])

    def test_unchanged_repair_stops_and_retains_previous_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = self.prepare(root, [BAD])
            with patch('candidate_repair.call_api', return_value=(BAD + '\n', {'usage': {}})) as mocked:
                repair_candidates(SimpleNamespace(max_functional_repairs=5), root, SPEC, contract(), rows)
            self.assertLessEqual(mocked.call_count, 2)
            self.assertFalse(rows[0]['directed']['passed'])
            self.assertEqual(rows[0]['functional_history'][-1]['status'], 'no_progress')

    def test_truncated_response_retries_with_larger_recorded_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(api_log_root=Path(tmp), model='mock', reasoning_effort='none', max_tokens=8192, temperature=0)
            with patch('candidate_runtime.call_llm', side_effect=[RuntimeError("Incomplete completion: 'length'; inspect API logs."), ('complete', {'usage': {}})]) as mocked:
                text, metadata = call_api(args, 'system', 'user')
            self.assertEqual(text, 'complete')
            self.assertEqual(mocked.call_args.kwargs['max_tokens'], 16384)
            self.assertEqual(mocked.call_args.kwargs['reasoning_effort'], 'none')
            self.assertEqual(metadata['request_attempts'], 2)

    def test_metrics_keep_initial_failure_separate_from_repaired_success(self):
        from run_three_candidate_select import aggregate
        candidate = {'candidate_id': 1, 'first_syntax_pass': True, 'final_syntax_pass': True,
                     'api_calls': 2, 'total_tokens': 20, 'initial_official': {'pass': False},
                     'official': {'pass': True}}
        row = {'candidates': [candidate], 'selection': {'selected_id': 1, 'api_calls': 0, 'total_tokens': 0},
               'selected_official': {'pass': True}}
        result = aggregate([row], SimpleNamespace(model='mock', reasoning_effort='none', temperature=0), ['test'])
        self.assertEqual(result['metrics']['pass_at_1_count'], 0)
        self.assertEqual(result['metrics']['oracle_pass_at_3_count'], 0)
        self.assertEqual(result['metrics']['oracle_after_repair_count'], 1)
        self.assertEqual(result['metrics']['selected_at_3_count'], 1)

if __name__ == '__main__':
    unittest.main()
