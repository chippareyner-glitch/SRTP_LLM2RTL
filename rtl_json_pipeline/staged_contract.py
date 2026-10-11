"""Generate a shared contract header, then bounded, independently reset scenarios."""
import json
from pathlib import Path
from .gates import parse_object
from .prompts import CONTRACT_SYSTEM


def generate_contract(user, directory, request):
    directory = Path(directory)

    def ask(instruction, payload, folder):
        folder.mkdir(parents=True, exist_ok=True)
        prompt = payload + '\n' + instruction
        (folder / 'prompt.json').write_text(json.dumps(
            {'system': CONTRACT_SYSTEM, 'user': prompt}, ensure_ascii=False, indent=2), encoding='utf-8')
        raw = request(CONTRACT_SYSTEM, prompt, folder)
        (folder / 'response.txt').write_text(raw, encoding='utf-8')
        return parse_object(raw)

    header = ask(
        'This is stage 1 of a multi-call generator. Return the contract root with scenarios=[] '
        'and an extra scenario_plan array (1 to 12 entries). Each entry has id, verifies, '
        'source_refs and objective. Define ALL shared models now. Preserve every requirement. '
        'Do not emit executable steps yet. Plan compact independent scenarios, each explicitly '
        'establishing DUT and model state. Use repeat for repetitive stimulus. '
        'Set timeout_ticks to cover the SUM of all planned scenarios plus settling time. '
        'The scenarios are generated in later calls. unsupported_reason remains allowed.',
        user, directory / 'plan')
    if header.get('unsupported_reason'):
        return json.dumps(header, ensure_ascii=False)
    plan = header.pop('scenario_plan', None)
    if not isinstance(plan, list) or not 1 <= len(plan) <= 12:
        raise ValueError('Staged contract needs 1 to 12 scenario_plan entries')
    ids = []
    for item in plan:
        if not isinstance(item, dict) or not all(k in item for k in ('id', 'verifies', 'source_refs', 'objective')):
            raise ValueError('Incomplete scenario plan')
        if not isinstance(item['id'], str) or item['id'] in ids:
            raise ValueError('Scenario plan IDs must be unique strings')
        ids.append(item['id'])
    header['scenarios'] = []
    shared = json.dumps(header, ensure_ascii=False)
    scenarios = []
    for index, item in enumerate(plan):
        part = ask(
            'This is a scenario generation stage. Return ONLY {"scenario":{id,verifies,source_refs,steps}} '
            'for the selected plan entry, or unsupported_reason. Copy id/verifies/source_refs exactly. '
            'Do not add or change shared definitions. Explicitly initialize model state and establish '
            'DUT state using legal stimulus; earlier scenarios leave state behind. Never assume the '
            'initial root values are reapplied between scenarios. Keep steps compact with repeat. '
            'If the shared definitions cannot express the test, return unsupported_reason.',
            user + '\nShared contract definitions:\n' + shared + '\nSelected scenario:\n' +
            json.dumps(item, ensure_ascii=False), directory / f'scenario_{index:02d}')
        if part.get('unsupported_reason'):
            return json.dumps(part, ensure_ascii=False)
        scenario = part.get('scenario')
        if not isinstance(scenario, dict) or any(scenario.get(k) != item[k] for k in ('id', 'verifies', 'source_refs')):
            raise ValueError('Generated scenario changed the selected plan identity or coverage')
        if not isinstance(scenario.get('steps'), list) or not scenario['steps']:
            raise ValueError('Generated scenario has no executable steps')
        scenarios.append(scenario)
    header['scenarios'] = scenarios
    raw = json.dumps(header, ensure_ascii=False)
    (directory / 'assembled_contract.json').write_text(raw, encoding='utf-8')
    return raw
