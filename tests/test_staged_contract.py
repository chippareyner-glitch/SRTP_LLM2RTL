import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_json_pipeline import contract
from rtl_json_pipeline.staged_contract import generate_contract
from rtl_json_pipeline.api import request_json


class StagedContractTests(unittest.TestCase):
    def test_assembles_separate_calls_with_shared_context(self):
        expected = contract()
        second = copy.deepcopy(expected['scenarios'][0])
        second['id'] = 'repeat_check'
        expected['scenarios'].append(second)
        header = copy.deepcopy(expected)
        header['scenarios'] = []
        header['scenario_plan'] = [dict((k, s[k]) for k in ('id','verifies','source_refs')) |
                                   {'objective':'Check inversion'} for s in expected['scenarios']]
        replies = iter([header] + [{'scenario':s} for s in expected['scenarios']])
        calls = []
        def request(system, user, folder):
            calls.append(user)
            return json.dumps(next(replies))
        with tempfile.TemporaryDirectory() as tmp:
            actual = json.loads(generate_contract('Original specification', tmp, request))
            self.assertEqual(actual, expected)
            self.assertEqual(len(calls), 3)
            self.assertTrue(all('Original specification' in c for c in calls))
            self.assertIn('Shared contract definitions', calls[1])
            self.assertTrue((Path(tmp)/'assembled_contract.json').exists())

    def test_changed_coverage_rejected(self):
        header = contract()
        header['scenario_plan'] = [{'id':'both','verifies':['R1'],'source_refs':['SRC002'],'objective':'invert'}]
        scenario = copy.deepcopy(header['scenarios'][0])
        scenario['verifies'] = []
        replies = iter([header, {'scenario':scenario}])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate_contract('spec', tmp, lambda *args:json.dumps(next(replies)))

    def test_default_no_reasoning_and_truncation_never_accepted(self):
        calls = []
        def invoke(*args, **kwargs):
            calls.append(kwargs)
            raise RuntimeError("Incomplete completion: 'length'; inspect API logs.")
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(RuntimeError):
                request_json('system','user',tmp,invoke=invoke)
        self.assertEqual(calls,[{'reasoning_effort':'none'}])
