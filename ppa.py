"""Final RTL synthesis assessment. Generic gates/depth are proxies, not physical PPA."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent


def positive_seconds(value):
    seconds = int(value)
    if seconds < 1:
        raise argparse.ArgumentTypeError('timeout must be a positive integer')
    return seconds


def add_ppa_arguments(parser, *, default_top='TopModule'):
    parser.add_argument('--ppa', choices=['generic', 'off'], default='generic',
                        help='Final generic synthesis assessment (default: generic)')
    parser.add_argument('--ppa-yosys', help='Yosys/YoWASP executable; also accepts PPA_YOSYS')
    parser.add_argument('--ppa-top', default=default_top,
                        help='Synthesis top module; RTLLM defaults to automatic discovery')
    parser.add_argument('--ppa-timeout', type=positive_seconds, default=120,
                        help='Synthesis timeout in seconds (default: 120)')


def find_yosys(configured=None):
    explicit = configured or os.environ.get('PPA_YOSYS')
    if explicit:
        candidate = shutil.which(str(explicit))
        if candidate:
            return str(Path(candidate).resolve())
        path = Path(explicit).expanduser()
        return str(path.resolve()) if path.is_file() else None
    for name in ('yosys', 'yowasp-yosys'):
        candidate = shutil.which(name)
        if candidate:
            return str(Path(candidate).resolve())
    for environment in ('.venv', '.venv312'):
        for relative in ('Scripts/yowasp-yosys.exe', 'bin/yowasp-yosys'):
            path = ROOT / 'tools/ppa' / environment / relative
            if path.is_file():
                return str(path)
    return None


def _save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def _text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''


def _metrics(directory, requested_top):
    stats = json.loads((directory / 'stats.json').read_text(encoding='utf-8'))
    netlist = json.loads((directory / 'netlist.json').read_text(encoding='utf-8'))
    modules = netlist['modules']
    if len(modules) != 1:
        raise ValueError('Expected one flattened synthesis top, without blackbox modules')
    top, module = next(iter(modules.items()))
    if requested_top and top != requested_top:
        raise ValueError('Synthesis top differs from the requested top')
    if any(int(str(module.get('attributes', {}).get(key, '0')), 2)
           for key in ('blackbox', 'whitebox')):
        raise ValueError('Top module is a blackbox')
    counts = Counter(cell['type'] for cell in module['cells'].values())
    # synth -flatten maps registers to single-bit generic sequential primitives.
    sequential = sum(count for kind, count in counts.items()
                     if 'DFF' in kind or 'LATCH' in kind or kind == '$_SR_')
    latches = sum(count for kind, count in counts.items() if 'LATCH' in kind)
    if any(not kind.startswith('$_') for kind in counts):
        raise ValueError('Unmapped or unsupported cells remain in the netlist')
    module_stats = stats['modules'].get('\\' + top) or stats['modules'].get(top)
    if not module_stats or module_stats['num_cells'] != sum(counts.values()):
        raise ValueError('Cell statistics and netlist disagree')
    depth_log = (directory / 'logic_depth.log').read_text(encoding='utf-8')
    depths = re.findall(r'Longest topological path in .*? \(length=(-?\d+)\)', depth_log)
    if len(depths) != 1:
        raise ValueError('Missing or ambiguous flattened logic-depth report')
    depth = int(depths[0])
    if depth < 0 and counts:
        raise ValueError('Invalid logic depth for a nonempty netlist')
    return top, {
        'cell_count': sum(counts.values()),
        'sequential_cells': sequential,
        'flip_flop_cells': sequential - latches - counts.get('$_SR_', 0),
        'latch_cells': latches,
        'combinational_cells': sum(counts.values()) - sequential,
        'cells_by_type': dict(sorted(counts.items())),
        'wire_count': module_stats['num_wires'],
        'wire_bits': module_stats['num_wire_bits'],
    }, max(depth, 0)


def assess_ppa(rtl_paths, output, *, top='TopModule', yosys=None, timeout=120,
               mode='generic', functional_passed=None, skip_reason=None):
    """Assess only supplied final RTL; never open official references/testbenches.

    Results have their own status. A synthesis error never changes functional_passed.
    Each output directory must be new, preventing stale reports from being reused.
    """
    directory = Path(output).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    result = {
        'schema_version': 1, 'backend': 'yosys_generic', 'status': 'pending',
        'assessment_scope': 'generic_synthesis_proxies', 'synthesis_passed': None,
        'functional_passed': functional_passed, 'requested_top': top,
        'resolved_top': None, 'sources': [], 'tool': None,
        'area': {'status': 'not_evaluated', 'unit': 'generic_cells',
                 'cell_count': None, 'physical_area_um2': None},
        'timing': {'status': 'not_evaluated', 'logic_depth': None,
                   'critical_path_ns': None, 'fmax_mhz': None},
        'power': {'status': 'not_evaluated', 'total_power_mw': None,
                  'reason': 'Requires a target library/device, operating conditions and switching activity'},
        'limitations': [
            'Generic cell counts are resource proxies, not physical area or FPGA LUT counts.',
            'Logic depth excludes sequential cells; it is not STA delay or Fmax.',
            'No target mapping, placement/routing, physical timing or power analysis is performed.',
            'Synthesis does not establish functional correctness.',
        ],
    }

    def finish(status, error=None):
        result['status'] = status
        if error:
            result['error'] = str(error)
        result['elapsed_seconds'] = round(time.monotonic() - started, 6)
        _save(directory / 'report.json', result)
        return result

    if mode == 'off':
        return finish('disabled')
    if skip_reason:
        return finish('skipped', skip_reason)
    try:
        if mode != 'generic' or timeout < 1:
            raise ValueError('Invalid synthesis mode or timeout')
        if top is not None and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*', top):
            raise ValueError('Invalid synthesis top identifier')
        paths = [Path(path).resolve() for path in rtl_paths]
        if not paths:
            return finish('skipped', 'No final RTL was produced')
        inputs = []
        for index, path in enumerate(paths):
            data = path.read_bytes()
            name = f'input_{index:03d}.sv'
            # Stage standalone RTL under fixed safe names, including on Windows/YoWASP.
            (directory / name).write_text(data.decode('utf-8-sig'), encoding='utf-8')
            result['sources'].append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                                      'staged_path': name})
            inputs.append(name)
        executable = find_yosys(yosys)
        if not executable:
            return finish('tool_unavailable', 'Install tools/ppa/requirements.txt or set --ppa-yosys / PPA_YOSYS')
        result['tool'] = {'executable': executable, 'version': None}
        script = '\n'.join([
            'read_verilog -sv ' + ' '.join(inputs),
            'hierarchy -check ' + ('-top ' + top if top else '-auto-top'),
            'flatten -noscopeinfo',
            'synth -flatten' + (' -top ' + top if top else ''),
            'check -assert',
            'tee -o stats.json stat -json',
            'write_json netlist.json',
            'write_verilog -noattr netlist.v',
            'tee -o logic_depth.log ltp -noff', '',
        ])
        (directory / 'synthesis.ys').write_text(script, encoding='utf-8')
        command = [executable, '-T', '-l', 'synthesis.log', '-s', 'synthesis.ys']
        result['command'] = command
        result['timeout_seconds'] = timeout
        environment = os.environ.copy()
        environment.setdefault('YOWASP_CACHE_DIR', str(ROOT / 'tools/ppa/cache'))
        process = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL,
                                 capture_output=True, timeout=timeout, encoding='utf-8', errors='replace',
                                 env=environment)
        launcher_log = process.stdout + '\n' + process.stderr
        (directory / 'launcher.log').write_text(launcher_log, encoding='utf-8')
        # YoWASP ABC can redirect stdout; use Yosys's own log and tee artifacts.
        log_path = directory / 'synthesis.log'
        if not log_path.is_file():
            log_path.write_text(launcher_log, encoding='utf-8')
        log = log_path.read_text(encoding='utf-8', errors='replace')
        result['returncode'] = process.returncode
        version = re.search(r'^\s*(Yosys [^\r\n]+)', log, re.M)
        result['tool']['version'] = version[1] if version else netlist_version(directory)
        if process.returncode != 0:
            result['synthesis_passed'] = False
            return finish('synthesis_failed', 'Yosys exited unsuccessfully; see synthesis.log')
        try:
            resolved_top, area, depth = _metrics(directory, top)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return finish('report_error', exc)
        result['resolved_top'] = resolved_top
        result['area'].update(area, status='proxy')
        result['timing'].update(logic_depth=depth, status='proxy')
        result['synthesis_passed'] = True
        return finish('ok')
    except subprocess.TimeoutExpired as exc:
        partial_log = _text(exc.stdout) + '\n' + _text(exc.stderr)
        (directory / 'launcher.log').write_text(partial_log, encoding='utf-8')
        if not (directory / 'synthesis.log').exists():
            (directory / 'synthesis.log').write_text(partial_log, encoding='utf-8')
        return finish('tool_timeout', f'Synthesis exceeded {timeout} seconds')
    except OSError as exc:
        return finish('tool_error' if result['tool'] else 'input_error', exc)
    except (ValueError, KeyError, TypeError) as exc:
        return finish('report_error', exc)


def netlist_version(directory):
    try:
        return json.loads((directory / 'netlist.json').read_text(encoding='utf-8')).get('creator')
    except (OSError, ValueError):
        return None


def final_ppa(args, rtl_path, output, *, functional_passed=None, skip_reason=None):
    """CLI adapter, also compatible with legacy/test argument namespaces."""
    return assess_ppa([rtl_path] if rtl_path else [], output,
                      top=getattr(args, 'ppa_top', 'TopModule'),
                      yosys=getattr(args, 'ppa_yosys', None),
                      timeout=getattr(args, 'ppa_timeout', 120),
                      mode=getattr(args, 'ppa', 'generic'),
                      functional_passed=functional_passed, skip_reason=skip_reason)


def write_ppa_csv(path, rows):
    """Rows are (case_id, variant, report); unavailable numeric fields stay blank."""
    with Path(path).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['case_id', 'variant', 'ppa_status', 'functional_passed', 'synthesis_passed',
                         'top', 'generic_cells', 'combinational_cells', 'flip_flop_cells',
                         'latch_cells', 'logic_depth', 'physical_area_um2', 'critical_path_ns',
                         'fmax_mhz', 'total_power_mw', 'error'])
        for case_id, variant, report in rows:
            area, timing, power = report['area'], report['timing'], report['power']
            writer.writerow([case_id, variant, report['status'], report['functional_passed'],
                             report['synthesis_passed'], report['resolved_top'], area['cell_count'],
                             area.get('combinational_cells'), area.get('flip_flop_cells'),
                             area.get('latch_cells'), timing['logic_depth'], area['physical_area_um2'],
                             timing['critical_path_ns'], timing['fmax_mhz'], power['total_power_mw'],
                             report.get('error', '')])


def write_summary_ppa_csv(path, results):
    rows = []
    for item in results:
        if 'ppa' in item:
            rows.append((item['case_id'], 'final', item['ppa']))
        for variant, value in item.items():
            if isinstance(value, dict) and 'ppa' in value:
                rows.append((item['case_id'], variant, value['ppa']))
    write_ppa_csv(path, rows)
