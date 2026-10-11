"""Open-source parser and simulator validation; no reference RTL is accessed."""
import json
import re
import subprocess
from pathlib import Path
from .analyzers import PyslangAnalyzer
from .contract_compiler import compile_testbench

def save(path, data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def validate(source, contract, directory, iverilog, vvp):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    (directory/'module.sv').write_text(source,encoding='utf-8')
    (directory/'testbench.sv').write_text(compile_testbench(contract),encoding='utf-8')
    result={'passed':False,'status':'pending','checks':0,'first_failure':None}
    def finish(status):
        result['status']=status;save(directory/'validation.json',result);return result
    try:
        analysis=PyslangAnalyzer().analyze(directory/'module.sv','TopModule')
        result['source_analysis']=analysis.to_dict()
        if not analysis.available:return finish('tool_unavailable')
        if not analysis.passed:return finish('source_analysis_failed')
        for stage,cmd in [('compile',[str(iverilog),'-g2012','-s','behavior_contract_tb','-o','sim.vvp','module.sv','testbench.sv']),('simulation',[str(vvp),'sim.vvp'])]:
            proc=subprocess.run(cmd,cwd=directory,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
            result[stage]={'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
            (directory/f'{stage}.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
            if stage=='compile' and proc.returncode:return finish('compile_failed')
        text=result['simulation']['stdout']+'\n'+result['simulation']['stderr']
        fail=re.search(r'CHECK_FAIL scenario=(\S+) label=(.*?) signal=(\S+) expected=(\S+) actual=(\S+)',text)
        if fail:result['first_failure']=dict(zip(['scenario','label','signal','expected','actual'],fail.groups()))
        result['trace']=[line for line in text.splitlines() if line.startswith('TRACE ')][-17:]
        passed=re.search(r'^BEHAVIOR_CONTRACT_PASS checks=(\d+)\s*$',text,re.M)
        result['checks']=int(passed[1]) if passed else 0
        if not passed:
            counts=re.findall(r'CHECKS_EXECUTED=(\d+)',text)
            if counts:result['checks']=int(counts[-1])
        result['passed']=bool(passed) and result['simulation']['returncode']==0 and result['checks']>0 and not fail and 'BEHAVIOR_CONTRACT_TIMEOUT' not in text
        return finish('pass' if result['passed'] else 'functional_failed')
    except subprocess.TimeoutExpired as exc:
        result['error']=f'{exc.cmd[0]} exceeded wall-clock limit';return finish('tool_timeout')
    except OSError as exc:
        result['error']=str(exc);return finish('tool_unavailable')

def mutation_gate(contract,directory,iverilog,vvp):
    """Reject trivially vacuous verifiers using constant-zero and constant-one DUTs."""
    ports=contract['module']['ports']; outcomes=[]
    for bit in [0,1]:
        decl=', '.join(f"{p['direction']} wire [{p['width']-1}:0] {p['name']}" for p in ports)
        assigns='\n'.join(f"assign {p['name']} = '{bit};" for p in ports if p['direction']=='output')
        source=f'module TopModule({decl});\n{assigns}\nendmodule\n'
        result=validate(source,contract,Path(directory)/f'constant_{bit}',iverilog,vvp)
        outcomes.append(result)
        if result['status'] in {'tool_unavailable','tool_timeout','source_analysis_failed','compile_failed'}:
            return {'passed':False,'status':'verifier_preflight_failed','results':outcomes}
    # A constant-output spec can legitimately accept one constant DUT. Both is vacuous.
    rejected=any(r['status']=='functional_failed' and r.get('first_failure') for r in outcomes)
    return {'passed':bool(rejected),'status':'pass' if rejected else 'verifier_suspect','results':outcomes}

def environment_check(directory,iverilog,vvp):
    """Compile and simulate a known fixture in the actual output filesystem."""
    contract={'module':{'ports':[{'name':'a','direction':'input','width':1},{'name':'q','direction':'output','width':1}]},
              'models':[],'clocks':[],'initial':{'a':"1'b0"},'timeout_ticks':100,
              'scenarios':[{'id':'environment','steps':[{'op':'delay','ticks':1},
                  {'op':'expect','label':'inverter','values':{'q':"1'b1"}}]}]}
    result=validate('module TopModule(input a,output q);assign q=~a;endmodule',contract,Path(directory),iverilog,vvp)
    return result
