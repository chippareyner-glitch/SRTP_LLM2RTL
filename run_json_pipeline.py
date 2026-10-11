"""Spec -> independent JSON contract and DesignIR -> deterministic RTL/TB -> validation."""
import argparse
import csv
from datetime import datetime
import importlib.util
import json
from pathlib import Path
from config import DATASET_DIR,IVERILOG,VVP,ARK_MODEL
from rtl_json_pipeline.pipeline import run_case
from rtl_json_pipeline.validation import save,environment_check
from ppa import add_ppa_arguments, final_ppa, find_yosys, write_summary_ppa_csv

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    selector=parser.add_mutually_exclusive_group()
    selector.add_argument('--cases',nargs='+')
    selector.add_argument('--all',action='store_true')
    parser.add_argument('--check',action='store_true',help='Offline tool and dataset check')
    parser.add_argument('--dataset',type=Path,default=DATASET_DIR)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--max-repairs',type=int,default=5,help='Max DesignIR repairs, up to N+1 candidates')
    parser.add_argument('--rtl-prompt',choices=['g3','baseline'],help='Generate RTL directly instead of DesignIR')
    add_ppa_arguments(parser)
    args=parser.parse_args()
    if args.max_repairs<0:parser.error('--max-repairs must be >= 0')
    files=sorted(args.dataset.glob('*_prompt.txt'))
    cases={p.name.removesuffix('_prompt.txt'):p for p in files}
    if args.cases:
        selected={}
        for prefix in args.cases:
            matches=[cid for cid in cases if cid==prefix or cid.startswith(prefix+'_')]
            if len(matches)!=1:parser.error(f'Ambiguous or missing case: {prefix}')
            selected[matches[0]]=cases[matches[0]]
        cases=selected
    tools_ok=Path(IVERILOG).is_file() and Path(VVP).is_file() and importlib.util.find_spec('pyslang') is not None
    if args.check:
        check_dir=Path(__file__).resolve().parent/'experiments'/datetime.now().strftime('tool_check_%Y%m%d_%H%M%S_%f')
        smoke=environment_check(check_dir,Path(IVERILOG),Path(VVP)) if tools_ok else {'passed':False,'status':'tool_unavailable'}
        tools_ok=tools_ok and smoke['passed']
        print(json.dumps(dict(cases=len(cases),model=ARK_MODEL,iverilog=IVERILOG,vvp=VVP,pyslang=bool(importlib.util.find_spec('pyslang')),tools_ready=tools_ok,actual_simulation=smoke['status'],logs=str(check_dir),ppa_mode=args.ppa,ppa_tool=find_yosys(args.ppa_yosys)),ensure_ascii=False,indent=2))
        return 0 if cases and tools_ok else 1
    if not args.cases and not args.all:parser.error('Choose --cases or --all (or --check)')
    if not cases:parser.error('Dataset has no specs')
    if not tools_ok:parser.error('Missing tools; run --check and install requirements-json.txt')
    out=(args.output or Path(__file__).resolve().parent/'experiments'/datetime.now().strftime('json_pipeline_%Y%m%d_%H%M%S_%f')).resolve()
    out.mkdir(parents=True,exist_ok=False)
    startup=environment_check(out/'tool_check',Path(IVERILOG),Path(VVP))
    if not startup['passed']:
        save(out/'summary.json',{'batch_status':'environment_failed','completed':0,'total':len(cases),'error':startup})
        print(f'工具实测失败，未调用API。详情：{out / "tool_check/validation.json"}')
        return 1
    summary={'model':ARK_MODEL,'total':len(cases),'max_repairs':args.max_repairs,'results':[],'scoring':'spec_contract_only','reference_rtl_used':False}
    consecutive_api_errors=0
    categories_path=Path(__file__).resolve().parent/'case_categories.json'
    categories=json.loads(categories_path.read_text(encoding='utf-8')) if categories_path.exists() else {}
    for index,(cid,spec) in enumerate(cases.items(),1):
        print(f'[{index}/{len(cases)}] {cid}: JSON generation and spec-only validation',flush=True)
        try:
            options={}
            if args.rtl_prompt:
                from llm_client import call_llm
                from rtl_json_pipeline.pipeline import live_request
                from rtl_json_pipeline.prompts import CONTRACT_SYSTEM
                from rtl_json_pipeline.semantic_review import REVIEW_SYSTEM
                system=(Path(__file__).resolve().parent/'prompts/direct'/f'{args.rtl_prompt}.system.txt').read_text(encoding='utf-8').strip()
                def request(system_prompt,user,folder):
                    if system_prompt in (CONTRACT_SYSTEM, REVIEW_SYSTEM):
                        return live_request(system_prompt,user,folder)
                    return call_llm(system_prompt,user,reasoning_effort='none',max_tokens=8192,temperature=0.0,log_dir=folder/'api_logs')
                options=dict(rtl_system=system,request=request)
            r=run_case(cid,spec,out,Path(IVERILOG),Path(VVP),args.max_repairs,**options)
        except Exception as exc:
            r={'case_id':cid,'passed':False,'status':'pipeline_error','error':str(exc),'iterations':[]}
            (out/cid).mkdir(exist_ok=True);save(out/cid/'summary.json',r)
        final_rtl=out/cid/'final.sv'
        r['ppa']=final_ppa(args, final_rtl if final_rtl.is_file() else None, out/cid/'ppa',
                           functional_passed=r['passed'])
        save(out/cid/'summary.json',r)
        summary['results'].append(r);summary['completed']=len(summary['results'])
        summary['passed']=sum(x['passed'] for x in summary['results']);save(out/'summary.json',summary)
        write_summary_ppa_csv(out/'ppa_results.csv',summary['results'])
        with (out/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['题号','类别','迭代次数','语法是否通过','功能是否通过','报错原因'])
            for item in summary['results']:
                validations=[i['validation'] for i in item.get('iterations',[]) if 'validation' in i]
                last=validations[-1] if validations else {}
                syntax='通过' if last.get('compile',{}).get('returncode')==0 else '未判定' if not last else '未通过'
                writer.writerow([item['case_id'],categories.get(item['case_id'],'未分类'),len(validations),syntax,'通过（规格契约）' if item['passed'] else '未通过' if validations else '未判定',item.get('error') or ('' if item['passed'] else item['status'])])
        print(f"{cid}: {r['status']}",flush=True)
        consecutive_api_errors=consecutive_api_errors+1 if r['status'] in {'contract_api_error','design_api_error'} else 0
        if consecutive_api_errors>=3:
            summary['batch_status']='stopped_api_errors'
            summary['not_attempted']=[c for c in cases if c not in {x['case_id'] for x in summary['results']}]
            save(out/'summary.json',summary)
            print('连续3题API失败，停止批次；未尝试的题不记为代码失败。',flush=True)
            break
    print(f'Results: {out}')
    return 0 if summary['passed']==len(cases) else 1

if __name__=='__main__':raise SystemExit(main())
