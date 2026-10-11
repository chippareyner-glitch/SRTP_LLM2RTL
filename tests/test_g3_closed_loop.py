import json
import tempfile
import unittest
from pathlib import Path
from test_json_pipeline import contract, SPEC
from config import IVERILOG, VVP
from rtl_json_pipeline.pipeline import run_case


class G3ClosedLoopTests(unittest.TestCase):
    def run_replies(self, replies):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); spec=root/'spec.txt';spec.write_text(SPEC)
            values=iter([json.dumps(contract()),*replies]); calls=[]
            def request(system,user,folder):
                from rtl_json_pipeline.semantic_review import REVIEW_SYSTEM
                if system==REVIEW_SYSTEM:
                    return json.dumps({'verdict':'accept','issues':[],'evidence':['Both Boolean input values are checked against the specification.']})
                calls.append((system,user));return next(values)
            result=run_case('test',spec,root,Path(IVERILOG),Path(VVP),5,request,rtl_system='Generate RTL')
            self.assertEqual(json.loads((root/'test/frozen_contract.json').read_text()),contract())
            return result,calls

    def test_functional_repair(self):
        result,calls=self.run_replies(['module TopModule(input a,output q);assign q=a;endmodule',
                                     'module TopModule(input a,output q);assign q=~a;endmodule'])
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['validation_rounds'],2)
        self.assertEqual(len(calls),3)
        self.assertIn('first_failure',calls[-1][1])
        self.assertFalse(result['reference_rtl_used'])
        self.assertGreater(result['iterations'][0]['validation']['checks'],0)
        self.assertTrue(result['iterations'][0]['validation']['trace'])

    def test_semantically_invalid_contract_never_generates_rtl(self):
        from rtl_json_pipeline.semantic_review import REVIEW_SYSTEM
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);spec=root/'spec.txt';spec.write_text(SPEC)
            calls=[]
            def request(system,user,folder):
                calls.append(system)
                if system==REVIEW_SYSTEM:
                    return json.dumps({'verdict':'revise','issues':['Expected value contradicts source'],
                                       'evidence':['Input a=0 requires q=1']})
                return json.dumps(contract())
            result=run_case('test',spec,root,Path(IVERILOG),Path(VVP),5,request,rtl_system='Generate RTL')
            self.assertEqual(result['status'],'contract_invalid')
            self.assertEqual(result['generation_attempts'],0)
            self.assertNotIn('Generate RTL',calls)
            self.assertTrue((root/'test/contract/attempt_01/semantic_review/review.json').exists())

    def test_repeated_candidate_stops(self):
        bad='module TopModule(input a,output q);assign q=a;endmodule'
        result,_=self.run_replies([bad,bad])
        self.assertEqual(result['status'],'no_progress')
        self.assertEqual(result['validation_rounds'],1)
