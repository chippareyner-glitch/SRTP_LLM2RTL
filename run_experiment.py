"""Reproducible DeepSeek spec-to-RTL entry point. Never overwrites v2 results."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from config import DATASET_DIR, IVERILOG, VVP, ARK_MODEL
from llm_client import call_llm
from code_gen import extract_code_from_response
from code_eval import evaluate_candidate
from ppa import add_ppa_arguments, final_ppa, find_yosys, write_summary_ppa_csv

ROOT=Path(__file__).resolve().parent
SYSTEM='''Implement the provided hardware specification as synthesizable SystemVerilog-2012.
Return only the complete TopModule and any necessary helper modules in one systemverilog code block.
Respect exact port names, widths, bit ordering, reset polarity and cycle timing.
Do not invent reset ports, initialization requirements or extra behavior absent from the specification.
Do not include a testbench, RefModule, $finish, $fatal, or $stop.'''

def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true',help='Offline environment check; no API charge')
    group.add_argument('--smoke',action='store_true',help='One small paid API request')
    group.add_argument('--case',help='Full case ID or unique prefix such as Prob001')
    group.add_argument('--all',action='store_true')
    parser.add_argument('--dataset',type=Path,default=DATASET_DIR)
    parser.add_argument('--max-repairs',type=int,default=0)
    parser.add_argument('--output',type=Path,help='New, non-existing output directory')
    parser.add_argument('--resume',action='store_true',help='Continue an existing output; completed cases including failed generations are retained')
    parser.add_argument('--report',type=Path,help='Excel output; defaults to 数据.xlsx in experiment directory')
    add_ppa_arguments(parser)
    args=parser.parse_args()
    if args.max_repairs<0: parser.error('--max-repairs must be non-negative')
    if args.check:
        import llm_client
        info=dict(python=sys.executable,model=ARK_MODEL,key_configured=bool(llm_client.ARK_API_KEY),
            iverilog=Path(IVERILOG).exists(),vvp=Path(VVP).exists(),dataset=str(args.dataset.resolve()),
            cases=len(list(args.dataset.glob('*_prompt.txt'))),ppa_mode=args.ppa,ppa_tool=find_yosys(args.ppa_yosys))
        print(json.dumps(info,ensure_ascii=False,indent=2)); return 0 if all([info['key_configured'],info['iverilog'],info['vvp'],info['cases']]) else 1
    dest=(args.output or ROOT/'experiments'/datetime.now().strftime('deepseek_%Y%m%d_%H%M%S_%f')).resolve()
    if args.resume and not args.output: parser.error('--resume requires --output')
    dest.mkdir(parents=True,exist_ok=args.resume)
    os.environ['LLM_LOG_DIR']=str(dest/'api_logs')
    if args.smoke:
        os.environ['DEEPSEEK_MAX_TOKENS']='1024'
        os.environ['DEEPSEEK_REASONING_EFFORT']='none'
        result=call_llm('Answer briefly.','Reply with OK.')
        write_json(dest/'smoke.json',dict(model=ARK_MODEL,response=result))
        print(f'API OK. Result: {dest}'); return 0
    cases=sorted(p.name.removesuffix('_prompt.txt') for p in args.dataset.glob('*_prompt.txt'))
    if args.case:
        cases=[c for c in cases if c==args.case or c.startswith(args.case+'_')]
        if len(cases)!=1: parser.error('Case prefix must identify exactly one task')
    if not cases: parser.error('No tasks found')
    summary={'model':ARK_MODEL,'dataset':str(args.dataset.resolve()),'max_repairs':args.max_repairs,'results':[]}
    if args.resume:
        previous=json.loads((dest/'summary.json').read_text(encoding='utf-8'))
        if any(previous.get(k)!=summary[k] for k in ['model','dataset','max_repairs']):
            parser.error('Resume settings differ from the saved experiment')
        summary=previous
    completed_ids={r['case_id'] for r in summary['results']}
    for cid in cases:
        if cid in completed_ids: continue
        case_dir=dest/cid; case_dir.mkdir()
        item={'case_id':cid,'attempts':[],'status':'pending'}
        try:
            inputs={kind:args.dataset/f'{cid}_{suffix}' for kind,suffix in [('prompt','prompt.txt'),('testbench','test.sv'),('reference','ref.sv')]}
            hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in inputs.items()}
            write_json(case_dir/'inputs.json',dict(paths={k:str(p.resolve()) for k,p in inputs.items()},sha256=hashes))
            spec=inputs['prompt'].read_text(encoding='utf-8-sig')
            (case_dir/'original_spec.txt').write_text(spec,encoding='utf-8')
            prompt=spec
            for attempt in range(args.max_repairs+1):
                attempt_dir=case_dir/f'attempt_{attempt:02d}'; attempt_dir.mkdir()
                (attempt_dir/'prompt.txt').write_text(prompt,encoding='utf-8')
                raw=call_llm(SYSTEM,prompt)
                (attempt_dir/'response.txt').write_text(raw,encoding='utf-8')
                rtl=extract_code_from_response(raw)
                path=attempt_dir/'module.sv'; path.write_text(rtl,encoding='utf-8')
                if not re.search(r'\bmodule\s+TopModule\b',rtl) or re.search(r'\bmodule\s+RefModule\b|\$(?:finish|stop|fatal)\b',rtl):
                    evaluation=dict(status='invalid_output',func_pass=False,error_text='Missing TopModule or forbidden reference/test termination code.')
                else:
                    evaluation=evaluate_candidate(str(path),str(inputs['testbench']),str(inputs['reference']),cid,tag='eval')
                write_json(attempt_dir/'evaluation.json',evaluation)
                item['attempts'].append(evaluation); item['status']=evaluation['status']
                if evaluation['func_pass']:
                    shutil.copyfile(path,case_dir/'module_final.sv'); break
                prompt=f'{spec}\n\nPrevious RTL:\n{rtl}\n\nEvaluation feedback:\n{evaluation.get("error_text","")}\n\nRepair the RTL while preserving the original specification.'
        except Exception as e:
            item['status']='error'; item['error']=str(e)
        final_rtl=case_dir/'module_final.sv'
        item['ppa']=final_ppa(args,final_rtl if final_rtl.is_file() else None,case_dir/'ppa',
                              functional_passed=any(a.get('func_pass') for a in item['attempts']))
        write_json(case_dir/'result.json',item)
        summary['results'].append(item)
        summary['total']=len(cases); summary['completed']=len(summary['results'])
        summary['initial_pass']=sum(bool(r['attempts'] and r['attempts'][0].get('func_pass')) for r in summary['results'])
        summary['final_pass']=sum(any(a.get('func_pass') for a in r['attempts']) for r in summary['results'])
        write_json(dest/'summary.json',summary)
        write_summary_ppa_csv(dest/'ppa_results.csv',summary['results'])
        print(f'{cid}: {item["status"]} ({summary["completed"]}/{len(cases)})',flush=True)
        if item['status']=='error' and not str(item.get('error','')).startswith(('Incomplete completion:','Empty final content')):
            from export_results import export_report
            export_report(dest,args.report)
            print('Stopped after error; inspect summary.json before retrying.'); return 1
    from export_results import export_report
    export_report(dest,args.report)
    print(f'Results: {dest}'); return 0

if __name__=='__main__':
    sys.exit(main())
