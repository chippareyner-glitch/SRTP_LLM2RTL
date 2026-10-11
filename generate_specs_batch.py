"""Generate RTL directly from each spec, without review, simulation or repair."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from config import DATASET_DIR, ARK_MODEL
from code_gen import code_gen

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=DATASET_DIR)
    parser.add_argument('--output', type=Path, help='New output directory')
    parser.add_argument('--check', action='store_true', help='List input count without calling the API')
    args = parser.parse_args()
    specs = sorted(args.dataset.glob('*_prompt.txt'))
    if not specs:
        parser.error(f'No *_prompt.txt files in {args.dataset}')
    # Validate readability before starting any paid requests.
    for spec in specs:
        if not spec.read_text(encoding='utf-8-sig').strip():
            parser.error(f'Empty spec: {spec}')
    print(f'Dataset: {args.dataset.resolve()}\nSpecs: {len(specs)}\nModel: {ARK_MODEL}', flush=True)
    if args.check:
        return 0
    output = (args.output or Path(__file__).resolve().parent / 'experiments' /
              datetime.now().strftime('direct_batch_%Y%m%d_%H%M%S_%f')).resolve()
    output.mkdir(parents=True, exist_ok=False)
    summary = dict(model=ARK_MODEL, dataset=str(args.dataset.resolve()), total=len(specs),
                   completed=0, generated=0, failed=0, results=[])
    for index, spec in enumerate(specs, 1):
        cid = spec.name.removesuffix('_prompt.txt')
        case_dir = output / cid
        case_dir.mkdir()
        os.environ['LLM_LOG_DIR'] = str(case_dir / 'api_logs')
        (case_dir / 'spec.txt').write_text(spec.read_text(encoding='utf-8-sig'), encoding='utf-8')
        print(f'[{index}/{len(specs)}] {cid}', flush=True)
        error = None
        try:
            status = code_gen(str(case_dir / 'spec.txt'), case_dir)
            if status != 'success':
                error_path = case_dir / 'spec_error.txt'
                error = error_path.read_text(encoding='utf-8') if error_path.exists() else 'Generation failed'
        except Exception as exc:
            status, error = 'error', str(exc)
            (case_dir / 'spec_error.txt').write_text(error, encoding='utf-8')
        summary['results'].append(dict(case_id=cid, status=status, error=error,
                                       validation='not_run'))
        summary['completed'] += 1
        summary['generated' if status == 'success' else 'failed'] += 1
        (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Results: {output}\nGenerated: {summary["generated"]}; failed: {summary["failed"]}. No validation performed.')
    return 1 if summary['failed'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
