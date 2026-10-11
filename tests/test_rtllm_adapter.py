import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rtllm_validator import verdict
import run_rtllm


class RTLLMTests(unittest.TestCase):
    def test_verdict_requires_success_and_no_failure(self):
        self.assertEqual(verdict('Your Design Passed',0,False),'pass')
        self.assertNotEqual(verdict('Your Design Passed\nError: mismatch',0,False),'pass')
        self.assertNotEqual(verdict('Your Design Passed',0,True),'pass')
        self.assertNotEqual(verdict('Your Design Passed',1,False),'pass')
        self.assertEqual(verdict('Test completed with 3/8 failures',0,False),'functional_failed')
        self.assertEqual(verdict('simulation finished',0,False),'unconfirmed')

    def test_generation_repair_and_reference_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); data=root/'data';data.mkdir();case=data/'invert';case.mkdir()
            (case/'spec.txt').write_text('Module invert: output q is complement of input a.')
            (case/'verified.v').write_text('module verified_invert; /* SECRET_REFERENCE */ endmodule')
            (data/'dataset_manifest.json').write_text(json.dumps({'cases':[{'name':'invert','category':'test',
                'directory':'invert','specification':'invert/spec.txt','references':['invert/verified.v'],'testbenches':[]}]}))
            outcomes=iter([{'syntax_pass':True,'func_pass':True,'status':'pass'},
                           {'syntax_pass':True,'func_pass':False,'status':'functional_failed'},
                           {'syntax_pass':True,'func_pass':True,'status':'pass'}])
            def validate(dataset,case,sources,folder,timeout):
                folder.mkdir(parents=True);(folder/'simulation.log').write_text('mismatch at output q')
                return next(outcomes)
            prompts=[]
            def llm(system,user,**kwargs):
                prompts.append(user)
                return 'module invert(input a,output q);assign q='+('a' if len(prompts)==1 else '~a')+';endmodule'
            out=root/'out'
            with patch('sys.argv',['run_rtllm','--all','--dataset',str(data),'--output',str(out),'--max-repairs','1']),\
                 patch('run_rtllm.validate_rtllm',side_effect=validate),patch('llm_client.call_llm',side_effect=llm):
                self.assertEqual(run_rtllm.main(),0)
            self.assertEqual(len(prompts),2)
            self.assertTrue(all('SECRET_REFERENCE' not in p for p in prompts))
            self.assertIn('mismatch at output q',prompts[1])
            result=json.loads((out/'summary.json').read_text())
            self.assertEqual(result['function_passed'],1)
