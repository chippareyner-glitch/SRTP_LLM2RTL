import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import closed_loop_enhanced_v2 as loop

class LegacyRecordsTest(unittest.TestCase):
    def run_fake(self, outcomes):
        with tempfile.TemporaryDirectory() as tmp:
            def generate(filename):
                Path(filename).with_name('module.sv').write_text('module TopModule; endmodule')
                return 'success'
            with patch.object(loop,'OUTPUT_BASE_DIR',Path(tmp)), patch.object(loop,'read_spec',return_value='spec'), patch.object(loop,'read_testbench',return_value='tb'), patch.object(loop,'read_reference',return_value='ref'), patch.object(loop,'code_gen',side_effect=generate), patch.object(loop,'enhanced_closed_loop_iteration',side_effect=outcomes):
                return loop.run_enhanced_closed_loop('test',max_iterations=len(outcomes))
    def test_failure_records_count(self):
        result=self.run_fake([(False,'old',{'status':'continued'}),(False,'old',{'status':'failed_max_iterations'})])
        self.assertEqual(result['iterations'],2)
    def test_api_failure_stops_without_fake_repair(self):
        result=self.run_fake([(False,'old',{'status':'reviewer_failed','error':'length'}),(True,'new',{'status':'success'})])
        self.assertEqual(result['iterations'],1)
        self.assertEqual(result['status'],'reviewer_failed')

if __name__=='__main__':unittest.main()
