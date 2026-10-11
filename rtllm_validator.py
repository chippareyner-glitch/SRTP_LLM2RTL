"""RTLLM adapter: isolated files, native testbench verdicts, bounded simulation."""
import json
import re
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from config import IVERILOG, VVP


def command(args, cwd, timeout):
    try:
        env = dict(os.environ)
        env['TMP'] = env['TEMP'] = str(Path(cwd).resolve())
        p = subprocess.run(list(map(str, args)), cwd=cwd, capture_output=True,
                           encoding='utf-8', errors='replace', timeout=timeout, env=env)
        return p.returncode, p.stdout + '\n' + p.stderr, False
    except subprocess.TimeoutExpired as e:
        def decode(s): return s.decode('utf-8', errors='replace') if isinstance(s, bytes) else (s or '')
        return -1, decode(e.stdout) + '\n' + decode(e.stderr), True


def verdict(text, rc, timed_out):
    if timed_out or re.search(r'\btimeout\b', text, re.I): return 'timeout'
    if rc != 0: return 'simulation_error'
    if re.search(r'\b(error|failed|fatal|mismatch)\b', text, re.I): return 'functional_failed'
    counts = re.findall(r'(\d+)\s*(?:/\s*\d+\s*)?failures', text, re.I)
    if any(int(n) for n in counts): return 'functional_failed'
    if re.search(r'Your\s+Design\s+Passed', text, re.I): return 'pass'
    return 'unconfirmed'


def validate_rtllm(dataset, case, sources, folder, timeout=30):
    # Windows Icarus builds can crash in Unicode working directories.
    with tempfile.TemporaryDirectory(prefix='rtllm_', dir=os.getenv('RTLLM_SCRATCH')) as temp:
        result = _validate(dataset, case, sources, Path(temp), timeout)
        shutil.copytree(temp, folder, dirs_exist_ok=True)
        return result


def _validate(dataset, case, sources, folder, timeout=30):
    folder = Path(folder).resolve(); folder.mkdir(parents=True, exist_ok=True)
    # Copy whole case to preserve data paths; never compile the copied reference implicitly.
    work = folder / 'work'
    shutil.copytree(Path(dataset)/case['directory'], work, dirs_exist_ok=True)
    srcs = []
    for i, source in enumerate(sources):
        p = work / f'candidate_{i}.sv'; p.write_text(source, encoding='utf-8'); srcs.append(p.name)
    rc, log, expired = command([IVERILOG, '-g2012', '-tnull', '-I', '.', *srcs], work, 60)
    log = f'returncode={rc}, timeout={expired}\n' + log
    (folder/'syntax.log').write_text(log, encoding='utf-8')
    result = {'syntax_pass':rc == 0 and not expired, 'func_pass':False}
    if not result['syntax_pass']:
        result['status'] = 'syntax_timeout' if expired else 'tool_crash' if rc > 255 or rc < 0 else 'syntax_failed'
    else:
        tbs = [Path(p).relative_to(case['directory']) for p in case['testbenches']]
        # Explicit tops exclude uninstantiated helper/reference modules.
        modules = []
        for tb in tbs:
            text = re.sub(r'/\*.*?\*/|//[^\n]*', '', (work/tb).read_text(encoding='utf-8'), flags=re.S)
            modules.extend(re.findall(r'\bmodule\s+(\w+)', text))
        sim = 'sim.vvp'
        rc, log, expired = command([IVERILOG, '-g2012', '-I', '.',
            *[v for name in modules for v in ('-s',name)], '-o', sim, *tbs, *srcs], work, 60)
        (folder/'compile.log').write_text(log, encoding='utf-8')
        if rc != 0 or expired: result['status'] = 'compile_failed'
        else:
            rc, log, expired = command([VVP, '-n', sim], work, timeout)
            (folder/'simulation.log').write_text(log, encoding='utf-8')
            result['status'] = verdict(log,rc,expired)
            result['func_pass'] = result['status'] == 'pass'
    (folder/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
