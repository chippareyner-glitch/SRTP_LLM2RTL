"""Spec-only contract preparation and executable candidate selection."""
import hashlib
import json
from pathlib import Path

from candidate_runtime import call_api, DEFAULT_IVERILOG, DEFAULT_VVP
from rtl_json_pipeline.gates import gate_contract, parse_object
from rtl_json_pipeline.source_registry import build_source_registry
from rtl_json_pipeline.prompts import CONTRACT_SYSTEM
from rtl_json_pipeline.validation import mutation_gate, validate, save

CONTRACT_AUDIT = '''Audit this test contract against the original spec only, without any candidate RTL.
Return the complete corrected contract in exactly the original schema.
Recompute every expected value. Prefer width-qualified expressions (256'd1 << 128)
over manually counting digits in long hex literals. Never infer power-on register values.
Synchronous reset requires an active edge; reset-free registers need a justified warmup sequence.
wait_edge includes one tick of NBA settling. Calculate cumulative delay: other clocks keep running.
Do not invent an interface-only functional expectation. Model updates must track every elapsed edge.
Check simultaneous controls, reset timing, bit ordering, boundary values and final-cycle outputs.
Use compact repeat/model operations. Do not remove real requirements just to make tests pass.
No oracle expression may read DUT outputs. Return unsupported_reason if spec cannot justify an oracle.'''


def select_with_generated_contract(args, case_id, case_out, spec, candidates):
    """The contract request sees only spec, never candidates or reference files."""
    registry = build_source_registry(spec)
    folder = case_out / 'contract'
    folder.mkdir()
    save(folder / 'source_registry.json', registry)
    base = json.dumps({'case_id': case_id, 'specification': spec, 'source_registry': registry}, ensure_ascii=False)
    feedback = ''
    contract = None
    calls = []
    error = ''
    status = 'contract_invalid'
    for attempt in range(2):
        stage = folder / f'attempt_{attempt:02d}'
        stage.mkdir()
        save(stage / 'prompt.json', {'system': CONTRACT_SYSTEM, 'user': base + feedback})
        try:
            raw, metadata = call_api(args, CONTRACT_SYSTEM, base + feedback)
            calls.append(metadata)
            save(stage / 'api.json', metadata)
            (stage / 'response.txt').write_text(raw, encoding='utf-8')
        except Exception as exc:
            error = str(exc)
            status = 'contract_api_error'
            break
        try:
            parsed = parse_object(raw)
            if parsed.get('unsupported_reason'):
                error = parsed['unsupported_reason']
                status = 'contract_unsupported'
                break
            checked = gate_contract(parsed, registry, case_id)
            if getattr(args, 'contract_review', True):
                review_user = base + '\nContract to audit:\n' + json.dumps(checked, ensure_ascii=False)
                save(stage / 'review_prompt.json', {'system': CONTRACT_AUDIT, 'user': review_user})
                reviewed, review_meta = call_api(args, CONTRACT_AUDIT, review_user)
                calls.append(review_meta)
                save(stage / 'review_api.json', review_meta)
                (stage / 'review_response.txt').write_text(reviewed, encoding='utf-8')
                checked = gate_contract(parse_object(reviewed), registry, case_id)
            preflight = mutation_gate(checked, stage / 'preflight', DEFAULT_IVERILOG, DEFAULT_VVP)
            save(stage / 'preflight.json', preflight)
            if not preflight['passed']:
                raise ValueError('Verifier preflight failed: ' + json.dumps(preflight, ensure_ascii=False)[-12000:])
            contract = checked
            break
        except Exception as exc:
            error = str(exc)
            save(stage / 'error.json', {'error': error})
            feedback = '\nPrevious contract:\n' + raw + '\nCorrect the validation error without changing the spec:\n' + error

    result = {'status': status, 'selected_id': None, 'selection_method': 'generated_spec_contract',
              'official_feedback_seen': False, 'api_calls': len(calls),
              'total_tokens': sum((m.get('usage') or {}).get('total_tokens', 0) or 0 for m in calls)}
    if contract is None:
        result['error'] = error
        return result
    frozen_path = case_out / 'frozen_contract.json'
    save(frozen_path, contract)
    result['contract_sha256'] = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    for row in candidates:
        if not row['final_syntax_pass']:
            continue
        module = Path(row['module_path'])
        row['directed'] = validate(module.read_text(encoding='utf-8'), contract,
                                   module.parent / 'directed', DEFAULT_IVERILOG, DEFAULT_VVP)
        row['initial_directed'] = row['directed']
    from candidate_repair import repair_candidates
    repairs = repair_candidates(args, case_out, spec, contract, candidates)
    result['repair_outcome'] = repairs
    passing = [r['candidate_id'] for r in candidates if (r.get('directed') or {}).get('passed')]
    result.update(status='selected' if passing else 'no_candidate_passed',
                  selected_id=min(passing) if passing else None,
                  passing_candidate_ids=passing, tie_break='lowest_candidate_id_among_passing')
    if not passing and repairs['status'] == 'verifier_suspect':
        result.update(status='verifier_suspect', error=repairs['reason'])
    return result


def select_with_saved_contract(args, case_id, case_out, candidates):
    """Explicitly supplied, manually curated upstream directed-test fixtures."""
    from spec_directed_validator import run_contract, build_testbench
    contract_path = Path(args.contract_dir) / f'{case_id}.json'
    result = {'status': 'contract_missing', 'selected_id': None, 'api_calls': 0, 'total_tokens': 0,
              'selection_method': 'saved_spec_contract', 'official_feedback_seen': False}
    if not contract_path.is_file():
        result['error'] = f'No saved contract for {case_id}'
        return result
    contract = json.loads(contract_path.read_text(encoding='utf-8-sig'))
    if contract.get('case_id') != case_id:
        raise ValueError('Contract case_id does not match the requested case')
    build_testbench(contract, 'TopModule')  # Fail before any simulation if malformed.
    frozen = case_out / 'frozen_contract.json'
    save(frozen, contract)
    result['contract_sha256'] = hashlib.sha256(frozen.read_bytes()).hexdigest()
    def evaluate(module, directory):
        report = run_contract(frozen, args.dataset, directory, str(DEFAULT_IVERILOG), str(DEFAULT_VVP), 'TopModule', module)
        report['status'] = {'functional_failure': 'functional_failed', 'compile_error': 'compile_failed', 'infrastructure_error': 'tool_unavailable', 'timeout': 'tool_timeout'}.get(report['status'], report['status'])
        first = next((line for line in report.get('simulation_stdout', '').splitlines() if line.startswith('DIRECTED_FAIL|')), None)
        report['first_failure'] = {'detail': first} if first else None
        return report
    for row in candidates:
        if row['final_syntax_pass']:
            module = Path(row['module_path'])
            row['directed'] = evaluate(module, module.parent / 'directed')
            row['initial_directed'] = row['directed']
    from candidate_repair import repair_candidates
    spec = (case_out / 'original_spec.txt').read_text(encoding='utf-8')
    repairs = repair_candidates(args, case_out, spec, contract, candidates, evaluate=evaluate)
    result['repair_outcome'] = repairs
    passing = [r['candidate_id'] for r in candidates if (r.get('directed') or {}).get('passed')]
    result.update(status='selected' if passing else 'no_candidate_passed',
                  selected_id=min(passing) if passing else None,
                  passing_candidate_ids=passing, tie_break='lowest_candidate_id_among_passing',
                  contract_source='manually_curated_upstream_fixture')
    if not passing and repairs['status'] == 'verifier_suspect':
        result.update(status='verifier_suspect', error=repairs['reason'])
    return result
