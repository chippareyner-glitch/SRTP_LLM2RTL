import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_targeted_repair as runner


class TargetedRepairTests(unittest.TestCase):
    def test_only_functional_failures(self):
        args = SimpleNamespace(prompts=runner.ROOT/'repair_prompts_20261008', cases=None)
        cases = runner.select_cases(args)
        self.assertEqual(len(cases), 11)
        self.assertIn('Prob154_fsm_ps2data', [c['case_id'] for c in cases])
        self.assertNotIn('Prob099_m2014_q6c', [c['case_id'] for c in cases])

    def test_reject_alternatives_and_simulation_override(self):
        for raw in ['```sv\nmodule TopModule; endmodule\n```\n```sv\nmodule TopModule; endmodule\n```',
                    '```sv\nmodule TopModule; initial $finish; endmodule\n```']:
            with self.assertRaises(ValueError): runner.extract_candidate(raw)

    def test_feedback_and_success_artifact(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / 'tests') as temp:
            root=Path(temp)
            cid='Prob000_test'
            for suffix in ['prompt.txt','test.sv','ref.sv']:
                (root/f'{cid}_{suffix}').write_text('fixture', encoding='utf-8')
            (root/'prompt.md').write_text('Specific repair instructions', encoding='utf-8')
            args=SimpleNamespace(prompts=root,dataset=root,target='benchmark',max_repairs=1)
            entry={'case_id':cid,'batch':'test','prompt':'prompt.md','historical':{'status':'sim'}}
            fail={'status':'sim','func_pass':False,'error_text':'wrong inversion','mismatches':1,'samples':2}
            success={'status':'pass','func_pass':True,'error_text':'','mismatches':0,'samples':2}
            replies=[('```sv\nmodule TopModule; endmodule\n```',{}),
                     ('```sv\nmodule TopModule(input a, output q); assign q=~a; endmodule\n```',{})]
            with patch.object(runner,'call_api',side_effect=replies) as api, patch.object(runner,'evaluate_candidate',side_effect=[fail,success]):
                result=runner.run_case(args,entry,root)
            self.assertTrue(result['passed'])
            self.assertIn('wrong inversion',api.call_args_list[1].args[2])
            self.assertIn('~a',(root/cid/'module_final.sv').read_text())
            self.assertEqual(len(result['attempts']),2)

    def test_api_error_never_passes(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / 'tests') as temp:
            root=Path(temp); cid='Prob000_test'
            for suffix in ['prompt.txt','test.sv','ref.sv']:
                (root/f'{cid}_{suffix}').write_text('fixture',encoding='utf-8')
            (root/'p.md').write_text('repair',encoding='utf-8')
            args=SimpleNamespace(prompts=root,dataset=root,target='benchmark',max_repairs=2)
            with patch.object(runner,'call_api',side_effect=RuntimeError('network failure')), patch.object(runner,'evaluate_candidate') as evaluate:
                result=runner.run_case(args,{'case_id':cid,'batch':'test','prompt':'p.md','historical':{}},root)
            self.assertFalse(result['passed'])
            self.assertEqual(result['status'],'api_error')
            evaluate.assert_not_called()
            self.assertFalse((root/cid/'module_final.sv').exists())


if __name__=='__main__': unittest.main()
