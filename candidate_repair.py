"""Repair RTL against a frozen spec-only verifier, with no official feedback."""
import hashlib
import json
import re
from pathlib import Path
from candidate_runtime import call_api, DEFAULT_IVERILOG, DEFAULT_VVP
from rtl_json_pipeline.validation import validate, save

FUNCTIONAL_SYSTEM = '''Repair the SystemVerilog RTL using only the original hardware specification,
frozen spec-derived verification contract, and failure evidence. Preserve the exact interface.
Explain nothing; return one complete synthesizable SystemVerilog code block.
Do not modify tests, add simulator tasks, force initial output values, or hardcode stimulus answers.
Check pre-edge nonblocking RHS, reset polarity, first/last cycles, priority, widths and signedness.
If evidence contradicts the original specification, return VERIFIER_SUSPECT followed by the reason
instead of changing valid behavior to satisfy an incorrect test.'''


MAX_DIAGNOSTICS = 12


def failure_signature(result):
    failure = result.get('first_failure')
    return json.dumps(failure, sort_keys=True) if failure else None


def compact_evidence(result):
    """Failure evidence for the repair prompt, bounded in size.

    The raw pyslang result lists every diagnostic with an absolute path; compiling a prose reply once put
    246K characters of it into a single repair prompt. Keep the first unique diagnostics and log tails.
    """
    evidence = {k: result.get(k) for k in ['status', 'first_failure', 'source_analysis', 'compile', 'compile_stderr']}
    analysis = evidence['source_analysis']
    if isinstance(analysis, dict):
        found = dict.fromkeys(f"line {d.get('line')} {d.get('severity')}: {d.get('message')}"
                              for d in analysis.get('diagnostics', []) if d.get('severity') in {'warning', 'error', 'fatal'})
        evidence['source_analysis'] = {'passed': analysis.get('passed'), 'diagnostics': list(found)[:MAX_DIAGNOSTICS],
                                       'omitted': max(0, len(found) - MAX_DIAGNOSTICS)} if found else None
    if isinstance(evidence['compile'], dict):
        evidence['compile'] = {k: v[-4000:] if isinstance(v, str) else v for k, v in evidence['compile'].items()}
    if isinstance(evidence['compile_stderr'], str):
        evidence['compile_stderr'] = evidence['compile_stderr'][-4000:]
    return evidence


def repair_candidates(args, case_out, spec, contract, candidates, evaluate=None):
    from run_spec_card_ab import extract_sv
    frozen = case_out / 'frozen_contract.json'
    original_hash = hashlib.sha256(frozen.read_bytes()).hexdigest()
    eligible = [c for c in candidates if c.get('final_syntax_pass')]
    signatures = [failure_signature(c.get('directed') or {}) for c in eligible]
    # Shared failure is a warning, never evidence of a correct DUT or of a wrong spec.
    if len(signatures) >= 2 and signatures[0] and len(set(signatures)) == 1:
        return {'status': 'verifier_suspect', 'reason': 'All eligible candidates fail the same assertion; review the verifier before modifying RTL.'}
    for row in eligible:
        row.setdefault('functional_repairs', 0)
        history = row.setdefault('functional_history', [])
        current = Path(row['module_path'])
        initial_source = current.read_text(encoding='utf-8')
        seen = {hashlib.sha256(initial_source.strip().encode()).hexdigest()}
        repeated = 0
        feedback_result = row['directed']
        working_source = initial_source
        for index in range(getattr(args, 'max_functional_repairs', 0)):
            result = feedback_result
            if result['passed'] or result['status'] in {'tool_unavailable', 'tool_timeout'}:
                break
            if hashlib.sha256(frozen.read_bytes()).hexdigest() != original_hash:
                raise RuntimeError('Frozen verification contract changed during repair')
            # module_path points into a previous stage after repair; keep rounds as siblings.
            stage = Path(row.setdefault('candidate_directory', str(current.parent))) / f'functional_repair_{index + 1:03d}'
            stage.mkdir()
            user = json.dumps({'specification': spec, 'frozen_contract': contract,
                               'rtl': working_source, 'failure': compact_evidence(result)}, ensure_ascii=False)
            save(stage / 'prompt.json', {'system': FUNCTIONAL_SYSTEM, 'user': user})
            record = {'repair_number': index + 1}
            history.append(record)
            row['functional_repairs'] += 1
            print(f"  candidate {row['candidate_id']} 功能修复 {index + 1}/{args.max_functional_repairs}", flush=True)
            try:
                raw, metadata = call_api(args, FUNCTIONAL_SYSTEM, user)
                (stage / 'response.txt').write_text(raw, encoding='utf-8')
                save(stage / 'api.json', metadata)
                row['api_calls'] += 1
                row['total_tokens'] += (metadata.get('usage') or {}).get('total_tokens', 0) or 0
                if raw.lstrip().startswith('VERIFIER_SUSPECT'):
                    record.update(status='verifier_suspect', error=raw)
                    save(stage / 'result.json', record)
                    break
                source = extract_sv(raw)
                if not re.search(r'\bmodule\b[\s\S]*\bendmodule\b', source):
                    # Prose-only reply: do not compile it or feed it back as the next round's "rtl".
                    record['status'] = 'no_rtl_in_reply'
                    save(stage / 'result.json', record)
                    continue
                digest = hashlib.sha256(source.strip().encode()).hexdigest()
                if digest in seen:
                    record['status'] = 'no_progress'
                    save(stage / 'result.json', record)
                    break
                seen.add(digest)
                (stage / 'candidate.sv').write_text(source, encoding='utf-8')
                checked = evaluate(stage / 'candidate.sv', stage / 'validation') if evaluate else validate(source, contract, stage / 'validation', DEFAULT_IVERILOG, DEFAULT_VVP)
                feedback_result = checked
                working_source = source
                record.update(status=checked['status'], validation=checked)
                # Retain a previously compiling candidate if the attempted repair cannot compile.
                if checked['status'] in {'pass', 'functional_failed'}:
                    current = stage / 'candidate.sv'
                    row['module_path'] = str(current)
                    row['directed'] = checked
                repeated = repeated + 1 if failure_signature(checked) and failure_signature(checked) == failure_signature(result) else 0
                if repeated >= 2:
                    record['stop_reason'] = 'repeated_failure_verifier_suspect'
                save(stage / 'result.json', record)
                if checked['passed'] or repeated >= 2:
                    break
            except Exception as exc:
                record.update(status='repair_error', error=str(exc))
                save(stage / 'result.json', record)
                break
        if row.get('candidate_directory'):
            (Path(row['candidate_directory']) / 'module_final.sv').write_text(current.read_text(encoding='utf-8'), encoding='utf-8')
    if not any((r.get('directed') or {}).get('passed') for r in eligible) and any(
        h.get('status') == 'verifier_suspect' or h.get('stop_reason') == 'repeated_failure_verifier_suspect'
        for r in eligible for h in r.get('functional_history', [])
    ):
        return {'status': 'verifier_suspect', 'reason': 'Repair found inconsistent test evidence or repeatedly failed the same assertion.'}
    return {'status': 'completed'}
