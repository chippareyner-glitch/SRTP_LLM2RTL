"""Offline synthesis assessment of saved RTL, without LLM requests."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from ppa import ROOT, add_ppa_arguments, assess_ppa, write_ppa_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rtl', type=Path, nargs='+', required=True,
                        help='Final RTL file(s); helper modules are synthesized together')
    parser.add_argument('--output', type=Path, help='New output directory')
    add_ppa_arguments(parser)
    args = parser.parse_args()
    output = args.output or ROOT / 'experiments' / datetime.now().strftime('ppa_%Y%m%d_%H%M%S_%f')
    report = assess_ppa(args.rtl, output, top=args.ppa_top, yosys=args.ppa_yosys,
                        timeout=args.ppa_timeout, mode=args.ppa)
    write_ppa_csv(output / 'ppa_results.csv', [(args.rtl[0].stem, 'saved_rtl', report)])
    print(json.dumps({'status': report['status'], 'generic_cells': report['area']['cell_count'],
                      'logic_depth': report['timing']['logic_depth'],
                      'report': str(output.resolve() / 'report.json')}, ensure_ascii=False, indent=2))
    return 0 if report['status'] in {'ok', 'disabled'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
