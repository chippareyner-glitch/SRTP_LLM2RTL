"""Generate RTLLM RTL using G3, validate with original testbenches, optionally repair."""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from validator import validate_rtllm
from ppa import add_ppa_arguments, final_ppa, write_summary_ppa_csv

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=ROOT.parent/'RTLLM_50_完整数据集')
    p.add_argument('--output',type=Path)
    p.add_argument('--cases',nargs='+')
    p.add_argument('--all',action='store_true')
    p.add_argument('--check',action='store_true',help='Reference preflight only; no API requests')
    p.add_argument('--max-repairs',type=int,default=0)
    p.add_argument('--timeout',type=int,default=30)
    add_ppa_arguments(p, default_top=None)
    args=p.parse_args()
    if args.max_repairs<0 or args.timeout<1:p.error('Invalid repair count or timeout')
    if not (args.all or args.cases or args.check):p.error('Choose --all, --cases or --check')
    dataset=args.dataset.resolve()
    cases=json.loads((dataset/'dataset_manifest.json').read_text(encoding='utf-8'))['cases']
    if args.cases:
        missing=set(args.cases)-{c['name'] for c in cases}
        if missing:p.error('Unknown cases: '+str(sorted(missing)))
        cases=[c for c in cases if c['name'] in args.cases]
    out=(args.output or ROOT/'experiments'/datetime.now().strftime('rtllm_%Y%m%d_%H%M%S_%f')).resolve()
    out.mkdir(parents=True,exist_ok=False)
    summary={'dataset':str(dataset),'total':len(cases),'max_repairs':args.max_repairs,
             'mode':'reference_check' if args.check else 'g3_native_testbench',
             'official_feedback_used_for_repair':args.max_repairs>0,'results':[]}
    system=(ROOT/'prompts/direct/g3.system.txt').read_text(encoding='utf-8')
    system+='\nUse the module names and interfaces from the specification. Include all required RTL submodules. Return all RTL in one code block. Do not emit testbenches, simulation system tasks, file I/O, or external includes.'
    consecutive_api_errors=0
    for i,case in enumerate(cases,1):
        print(f"[{i}/{len(cases)}] {case['name']}",flush=True)
        folder=out/case['name'];folder.mkdir()
        row={'case_id':case['name'],'category':case['category'],'iterations':[]}
        try:
            refs=[(dataset/f).read_text(encoding='utf-8') for f in case['references']]
            renames={name:name.removeprefix('verified_') for source in refs
                     for name in re.findall(r'\bmodule\s+(verified_\w+)',source)}
            aliases={'adder_pipe_64bit':{'verified_adder_64bit':'adder_pipe_64bit'},
                     'multi_pipe_4bit':{'verified_multi_pipe':'multi_pipe_4bit'}}
            renames.update(aliases.get(case['name'],{}))
            refs=[re.sub(r'\b\w+\b',lambda m:renames.get(m[0],m[0]),source) for source in refs]
            save(folder/'reference_module_mapping.json',renames)
            baseline=validate_rtllm(dataset,case,refs,folder/'reference',args.timeout)
            row['reference']=baseline
            if args.check:row['status']=baseline['status']
            else:
                from llm_client import call_llm
                spec=(dataset/case['specification']).read_text(encoding='utf-8')
                (folder/'spec.txt').write_text(spec,encoding='utf-8')
                feedback='';seen=set()
                for attempt in range(args.max_repairs+1):
                    trial=folder/f'iteration_{attempt:03d}';trial.mkdir()
                    user=spec+feedback
                    save(trial/'prompt.json',{'system':system,'user':user})
                    try:
                        raw=call_llm(system,user,case_id=case['name'],reasoning_effort='none',
                                     max_tokens=16384,temperature=0.0,log_dir=trial/'api_logs')
                    except Exception as exc:
                        row.update(status='api_error',error=str(exc));consecutive_api_errors+=1;break
                    consecutive_api_errors=0
                    (trial/'response.txt').write_text(raw,encoding='utf-8')
                    blocks=re.findall(r'```(?:systemverilog|verilog|sv)?\s*\n(.*?)```',raw,re.S|re.I)
                    code='\n'.join(blocks) if blocks else raw.strip()
                    clean=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
                    if not re.search(r'\bmodule\b',clean) or re.search(r'\$(?:display|write|finish|stop|fatal|readmem\w*|f\w+)\b|`include|\b(?:force|release|bind)\b',clean):
                        row['status']='invalid_generated_source';break
                    digest=hashlib.sha256(code.encode()).hexdigest()
                    if digest in seen:row['status']='no_progress';break
                    seen.add(digest)
                    (trial/'module.sv').write_text(code,encoding='utf-8')
                    (folder/'module.sv').write_text(code,encoding='utf-8')
                    result=validate_rtllm(dataset,case,[code],trial/'validation',args.timeout)
                    row['iterations'].append(result)
                    row.update(syntax_pass=result['syntax_pass'],func_pass=result['func_pass'] if baseline['func_pass'] else None,
                               status=result['status'] if baseline['func_pass'] else 'reference_failed')
                    if result['func_pass'] or not baseline['func_pass']:break
                    logs='\n'.join(f.read_text(encoding='utf-8') for f in (trial/'validation').glob('*.log'))
                    feedback='\nRepair this RTL according to the original specification:\n'+code+'\nValidator diagnostics:\n'+logs[-12000:]
        except Exception as exc:row.update(status='pipeline_error',error=str(exc))
        rtl=folder/'module.sv'
        row['ppa']=final_ppa(args,rtl if rtl.is_file() else None,folder/'ppa',
                             functional_passed=row.get('func_pass'),
                             skip_reason='Reference preflight does not assess generated RTL' if args.check else None)
        save(folder/'summary.json',row)
        summary['results'].append(row)
        summary.update(completed=len(summary['results']),syntax_passed=sum(r.get('syntax_pass') is True for r in summary['results']),
                       function_passed=sum(r.get('func_pass') is True for r in summary['results']))
        save(out/'summary.json',summary)
        write_summary_ppa_csv(out/'ppa_results.csv',summary['results'])
        with (out/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['case','category','status','syntax_pass','function_pass','candidates'])
            for r in summary['results']:writer.writerow([r['case_id'],r['category'],r['status'],r.get('syntax_pass'),r.get('func_pass'),len(r['iterations'])])
        print(row['status'],flush=True)
        if consecutive_api_errors>=3:
            summary['stopped_reason']='three_consecutive_api_errors';save(out/'summary.json',summary);break
    print(f'Results: {out}')
    return 0 if len(summary['results'])==len(cases) and all(r['status']=='pass' for r in summary['results']) else 1


if __name__=='__main__':raise SystemExit(main())
