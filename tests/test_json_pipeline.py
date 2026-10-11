import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from config import IVERILOG,VVP
from rtl_json_pipeline.pipeline import run_case
from rtl_json_pipeline.gates import gate_contract,gate_design
from rtl_json_pipeline.source_registry import build_source_registry
from rtl_json_pipeline.contract_compiler import compile_testbench
from rtl_json_pipeline.validation import validate
from rtl_json_pipeline.design_ir import render_systemverilog

SPEC='Input a is one bit. Output q is the complement of a.'
def contract():
    return {'schema_version':1,'case_id':'test','module':{'name':'TopModule','ports':[
        {'name':'a','direction':'input','width':1,'source_refs':['SRC001']},
        {'name':'q','direction':'output','width':1,'source_refs':['SRC002']}]},'clocks':[],
        'initial':{'a':"1'b0"},'models':[],
        'requirements':[{'id':'R1','text':'q complements a','source_refs':['SRC002']}],
        'scenarios':[{'id':'both','verifies':['R1'],'source_refs':['SRC002'],'steps':[
            {'op':'delay','ticks':1},{'op':'expect','label':'zero','values':{'q':"1'b1"}},
            {'op':'drive','values':{'a':"1'b1"}},{'op':'delay','ticks':1},
            {'op':'expect','label':'one','values':{'q':"1'b0"}}]}],'timeout_ticks':100}
def design(expr):
    return {'schema_version':1,'module':{'name':'TopModule','ports':[{'name':'a','direction':'input','width':1},{'name':'q','direction':'output','width':1}]},'design':{'kind':'combinational','signals':[],'outputs':[{'target':'q','expr':expr}]}}

class JSONPipelineTest(unittest.TestCase):
    def test_counter_and_bad_wrap(self):
        fixtures=Path(__file__).parent/'fixtures/json_pipeline'
        c=json.loads((fixtures/'counter_contract.json').read_text())
        ir=json.loads((fixtures/'counter_design.json').read_text())
        registry=[{'id':f'SRC{i:03d}'} for i in range(1,14)]
        gate_contract(c,registry,c['case_id']);gate_design(ir,c)
        with tempfile.TemporaryDirectory() as tmp:
            good=validate(render_systemverilog(ir),c,Path(tmp)/'good',Path(IVERILOG),Path(VVP))
            self.assertTrue(good['passed'],good)
            ir['design']['transitions'][0]['updates']['q']="4'd0"
            bad=validate(render_systemverilog(ir),c,Path(tmp)/'bad',Path(IVERILOG),Path(VVP))
            self.assertEqual(bad['status'],'functional_failed',bad)
    def test_handoff_one_line_module_reaches_functional_validation(self):
        c=contract()
        c['module']['ports']=[{'name':'clk','direction':'input','width':1,'source_refs':['SRC001']},{'name':'reset','direction':'input','width':1,'source_refs':['SRC001']},{'name':'q','direction':'output','width':4,'source_refs':['SRC002']}]
        c['clocks']=[{'signal':'clk','initial':0,'half_period':5,'source_refs':['SRC001']}]
        c['initial']={'reset':"1'b1"}
        c['scenarios'][0]['steps']=[{'op':'wait_edge','signal':'clk','edge':'posedge'},{'op':'expect','label':'reset','values':{'q':"4'd0"}}]
        with tempfile.TemporaryDirectory() as tmp:
            r=validate("module TopModule(input logic clk,input logic reset,output logic [3:0] q); assign q=4'd1; endmodule\n",c,Path(tmp)/'check',Path(IVERILOG),Path(VVP))
            self.assertEqual(r['status'],'functional_failed',r)
    def test_oracle_cannot_read_dut(self):
        c=contract();c['scenarios'][0]['steps'][1]['values']['q']='q'
        with self.assertRaises(ValueError):gate_contract(c,build_source_registry(SPEC),'test')
    def test_empty_scenario_is_not_coverage(self):
        c=contract();c['scenarios'][0]['steps']=[{'op':'delay','ticks':1}]
        with self.assertRaises(ValueError):gate_contract(c,build_source_registry(SPEC),'test')
    def test_raw_rtl_rejected(self):
        with self.assertRaises(ValueError):gate_design({'systemverilog':'module TopModule; endmodule'},contract())
    def test_statement_injection_rejected(self):
        with self.assertRaises(ValueError):gate_design(design('a; $finish'),contract())
    def test_real_simulator_repair_and_no_reference_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);spec=root/'spec.txt';spec.write_text(SPEC)
            replies=iter([contract(),design('a'),design('~a')]);prompts=[]
            def request(system,user,directory):
                prompts.append(user);return json.dumps(next(replies))
            r=run_case('test',spec,root/'out',Path(IVERILOG),Path(VVP),2,request)
            self.assertTrue(r['passed'],r)
            self.assertEqual(r['validation_rounds'],2)
            self.assertFalse(r['reference_rtl_used'])
            self.assertEqual(r['iterations'][0]['validation']['first_failure']['signal'],'q')
            self.assertIn('~a',(root/'out/test/final.sv').read_text())
    def test_api_error_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);spec=root/'spec.txt';spec.write_text(SPEC)
            def fail(*args):raise RuntimeError('connection interrupted')
            r=run_case('test',spec,root/'out',Path(IVERILOG),Path(VVP),1,fail)
            self.assertEqual(r['status'],'contract_api_error')
            self.assertEqual(r['validation_rounds'],0)
    def test_model_update_uses_old_values(self):
        c=contract();c['models']=[{'name':'x','width':1,'signed':False,'initial':"1'b0"},{'name':'y','width':1,'signed':False,'initial':"1'b1"}]
        c['scenarios'][0]['steps']=[{'op':'update_model','values':{'x':'y','y':'x'}},{'op':'delay','ticks':1},{'op':'expect','label':'swap','values':{'q':'x ^ y'}}]
        gate_contract(c,build_source_registry(SPEC),'test')
        with tempfile.TemporaryDirectory() as tmp:
            r=validate('module TopModule(input a,output q);assign q=1;endmodule',c,Path(tmp)/'eval',Path(IVERILOG),Path(VVP))
            self.assertTrue(r['passed'],r)
    def test_timeout_not_pass(self):
        c=contract();c['timeout_ticks']=1
        with tempfile.TemporaryDirectory() as tmp:
            r=validate('module TopModule(input a,output q);assign q=~a;endmodule',c,Path(tmp)/'eval',Path(IVERILOG),Path(VVP))
            self.assertFalse(r['passed'])

if __name__=='__main__':unittest.main()
