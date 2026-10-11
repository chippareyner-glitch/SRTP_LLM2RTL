"""Unified command dispatcher adapted from the September 27 handoff."""
import sys

def main():
    commands = {'rtllm': 'run_rtllm', 'direct': 'run_direct', 'generate': 'run_three_candidate_select', 'json': 'run_json_pipeline',
                'reselect': 'reselect_existing_candidates', 'select-contract': 'select_candidates_with_contract',
                'validate-contract': 'spec_directed_validator', 'ppa': 'run_ppa'}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print('Usage: python run.py {' + '|'.join(commands) + '} [arguments]')
        return 2
    import importlib
    command = sys.argv.pop(1)
    return importlib.import_module(commands[command]).main()

if __name__ == '__main__':
    raise SystemExit(main())
