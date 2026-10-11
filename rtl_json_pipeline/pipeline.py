"""Independent spec branches: frozen verification contract and repairable DesignIR."""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from .source_registry import build_source_registry
from .gates import parse_object,gate_contract,gate_design
from .design_ir import render_systemverilog
from .prompts import CONTRACT_SYSTEM,DESIGN_SYSTEM
from .validation import validate,mutation_gate,save
from .semantic_review import REVIEW_SYSTEM, parse_review

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def live_request(system,user,directory):
    from .api import request_json
    if system == CONTRACT_SYSTEM:
        from .staged_contract import generate_contract
        return generate_contract(user,directory,request_json)
    return request_json(system,user,directory)

def run_case(case_id,spec_path,output,iverilog,vvp,max_repairs=5,request=live_request,rtl_system=None):
    """request can be replayed in tests; only spec_path is opened from the dataset."""
    directory=Path(output)/case_id;directory.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    spec=Path(spec_path).read_text(encoding='utf-8-sig')
    (directory/'spec.txt').write_text(spec,encoding='utf-8')
    registry=build_source_registry(spec);save(directory/'source_registry.json',registry)
    result={'case_id':case_id,'passed':False,'status':'pending','reference_rtl_used':False,
            'official_testbench_used':False,'design_format':'DesignIR','iterations':[],'generation_attempts':0}
    if rtl_system:
        result.update(design_format='SystemVerilog',generation_prompt_sha256=hashlib.sha256(rtl_system.encode()).hexdigest())
    def finish(status,error=None):
        result['status']=status
        if error:result['error']=str(error)
        result['validation_rounds']=sum('validation' in i for i in result['iterations'])
        result['elapsed_seconds']=time.monotonic()-started
        logs=[json.loads(p.read_text(encoding='utf-8')) for p in directory.glob('**/api_logs/*.json')]
        result['recorded_usage']={key:sum((log.get('usage') or {}).get(key,0) or 0 for log in logs) for key in ['prompt_tokens','completion_tokens','total_tokens']}
        result['usage_note']='Only returned API metadata is counted; missing/interrupted request usage is unknown.'
        save(directory/'summary.json',result);return result
    def ask(system,user,folder):
        folder.mkdir(parents=True,exist_ok=True)
        save(folder/'prompt.json',{'system':system,'user':user})
        try:
            raw=request(system,user,folder)
            (folder/'response.txt').write_text(raw,encoding='utf-8')
            return raw
        except Exception as exc:
            save(folder/'api_error.json',{'type':type(exc).__name__,'error':str(exc)})
            raise
    base=json.dumps({'case_id':case_id,'specification':spec,'source_registry':registry},ensure_ascii=False)
    def audit(contract,folder,diagnostics=None):
        raw=ask(REVIEW_SYSTEM,json.dumps({'specification':spec,'source_registry':registry,
            'contract':contract,'diagnostics':diagnostics},ensure_ascii=False),folder)
        review=parse_review(raw);save(folder/'review.json',review);return review
    def stalled(reason):
        if not rtl_system:return finish('no_progress',reason)
        try:
            review=audit(contract,directory/'stall_review',{'reason':reason,'iterations':result['iterations'],
                'rtl':(directory/'module.sv').read_text(encoding='utf-8')})
        except Exception as exc:return finish('review_failed',exc)
        result['stall_review']=review
        return finish('verifier_suspect' if review['verdict']!='accept' else 'no_progress',reason)
    contract=None;feedback='';last_error=''
    for attempt in range(2):
        folder=directory/'contract'/f'attempt_{attempt:02d}'
        try:raw=ask(CONTRACT_SYSTEM,base+feedback,folder)
        except ValueError as exc:
            last_error=str(exc)
            save(folder/'schema_error.json',{'error':last_error})
            feedback='\nPrevious staged contract failed validation. Correct this error: '+last_error
            continue
        except Exception as exc:return finish('contract_api_error',exc)
        try:
            candidate=parse_object(raw)
            if candidate.get('unsupported_reason'):return finish('contract_unsupported',candidate['unsupported_reason'])
            checked=gate_contract(candidate,registry,case_id)
            if rtl_system:
                review=audit(checked,folder/'semantic_review')
                if review['verdict']!='accept':
                    raise ValueError('Contract semantic review requires revision: '+json.dumps(review,ensure_ascii=False))
            preflight=mutation_gate(checked,folder/'verifier_preflight',iverilog,vvp)
            save(folder/'verifier_preflight.json',preflight)
            if not preflight['passed']:
                failure=next((r for r in preflight['results'] if r['status'] in {'tool_unavailable','tool_timeout','source_analysis_failed','compile_failed'}),{})
                detail=failure.get('error') or failure.get('compile',{}).get('stderr') or str(failure.get('source_analysis') or preflight['status'])
                if failure.get('status') in {'tool_unavailable','tool_timeout'}:
                    return finish(preflight['status'],detail)
                raise ValueError('Contract testbench preflight failed: '+detail)
            contract=checked;break
        except Exception as exc:
            last_error=str(exc)
            save(folder/'schema_error.json',{'error':str(exc)})
            feedback='\nPrevious invalid JSON:\n'+raw+'\nCorrect these schema or semantic errors using only the original specification:\n'+str(exc)
    if contract is None:return finish('contract_invalid',last_error)
    save(directory/'frozen_contract.json',contract);contract_hash=digest(contract)
    result['contract_sha256']=contract_hash
    save(directory/'verifier_preflight.json',preflight)
    feedback=''; previous_hash=None; seen_hashes=set(); failure_counts={}
    for attempt in range(max_repairs+1):
        folder=directory/f'iteration_{attempt:03d}'
        user=json.dumps({'case_id':case_id,'specification':spec},ensure_ascii=False)+feedback
        system = (rtl_system if attempt == 0 else rtl_system + '\nRepair the current RTL using the frozen spec-only contract and diagnostics. Keep the original specification authoritative. Return complete RTL only; never change the contract or emit a testbench.') if rtl_system else DESIGN_SYSTEM
        try:raw=ask(system,user,folder)
        except Exception as exc:return finish('design_api_error',exc)
        result['generation_attempts']+=1
        record={'candidate_index':attempt,'repair_number':attempt}
        result['iterations'].append(record)
        try:
            if rtl_system:
                from code_gen import extract_code_from_response
                source=extract_code_from_response(raw)
                if not re.search(r'\bmodule\s+TopModule\b',source) or re.search(r'\$|\bRefModule\b|\b(?:force|release|bind)\b|`include',source):
                    raise ValueError('Expected standalone TopModule RTL without simulation system tasks, external includes or verification overrides')
                ir=source
            else:
                ir=parse_object(raw)
                if ir.get('unsupported_reason'):return finish('design_unsupported',ir['unsupported_reason'])
                gate_design(ir,contract);save(folder/'design_ir.json',ir)
                source=render_systemverilog(ir)
        except Exception as exc:
            record.update(status='design_invalid',error=str(exc));save(folder/'result.json',record)
            feedback='\nPrevious invalid candidate:\n'+raw+'\nValidation error:\n'+str(exc)
            continue
        code_hash=hashlib.sha256(source.encode()).hexdigest();record['rtl_sha256']=code_hash
        if code_hash in seen_hashes:
            record['status']='no_change';save(folder/'result.json',record)
            return stalled('Repair repeated an already failed candidate')
        previous_hash=code_hash
        seen_hashes.add(code_hash)
        # Keep the last rendered candidate for separate post-run benchmark evaluation.
        (directory/'module.sv').write_text(source,encoding='utf-8')
        if digest(contract)!=contract_hash or digest(json.loads((directory/'frozen_contract.json').read_text(encoding='utf-8')))!=contract_hash:
            return finish('contract_changed','Frozen contract changed during repair')
        evaluation=validate(source,contract,folder/'validation',iverilog,vvp)
        record.update(status=evaluation['status'],validation=evaluation);save(folder/'result.json',record)
        if evaluation['passed']:
            (directory/'module.sv').write_text(source,encoding='utf-8')
            (directory/'final.sv').write_text(source,encoding='utf-8')
            result['passed']=True;return finish('pass')
        if evaluation['status'] in {'tool_unavailable','tool_timeout'}:return finish(evaluation['status'])
        failure=evaluation.get('first_failure')
        if rtl_system and failure:
            key=tuple(failure.get(k) for k in ['scenario','label','signal'])
            failure_counts[key]=failure_counts.get(key,0)+1
            if failure_counts[key]>=3:return stalled('Three candidates failed at the same checkpoint')
        compact={k:evaluation.get(k) for k in ['status','first_failure','trace','checks','source_analysis','compile']}
        feedback='\nCurrent candidate:\n'+json.dumps(ir)+'\nFrozen spec-only test contract (cannot be changed):\n'+json.dumps(contract)+'\nValidation failure:\n'+json.dumps(compact)[-12000:]
        if rtl_system:feedback+='\nUse the recorded edge trace to identify the faulty state transition or data update. Check adjacent packets and reset recovery when applicable. Add a short RTL comment at the actual repair; do not change correct behavior to satisfy an inconsistent test.'
        save(directory/'summary.json',result)
    return finish('max_repairs_reached')
