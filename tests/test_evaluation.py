import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import code_eval
import code_val

class EvaluationTests(unittest.TestCase):
    def simulate(self, output, rc=0):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            files=[root/name for name in ['module.sv','test.sv','ref.sv']]
            for p in files: p.write_text('module m; endmodule')
            def command(cmd,**kwargs):
                if '-o' in cmd:
                    Path(cmd[cmd.index('-o')+1]).write_text('placeholder')
                    return 0,'','',False
                return rc,output,'',False
            with patch.object(code_eval,'run_cmd',side_effect=command):
                return code_eval.evaluate_candidate(*map(str,files),'test')

    def test_success_requires_samples(self):
        self.assertTrue(self.simulate('Mismatches: 0 in 20 samples')['func_pass'])
        self.assertFalse(self.simulate('Mismatches: 0 in 0 samples')['func_pass'])

    def test_unknown_and_timeout_are_not_pass(self):
        self.assertFalse(self.simulate('Simulation finished')['func_pass'])
        self.assertFalse(self.simulate('TIMEOUT\nMismatches: 0 in 20 samples')['func_pass'])

    def test_failed_process_cannot_pass(self):
        self.assertFalse(self.simulate('Mismatches: 0 in 20 samples',rc=1)['func_pass'])

    def test_mismatch(self):
        self.assertFalse(self.simulate('Mismatches: 1 in 20 samples')['func_pass'])

if __name__=='__main__': unittest.main()
