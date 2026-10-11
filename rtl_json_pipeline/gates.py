"""Conservative preflight gates; coverage is evidence, not a correctness proof."""
import json
import re
from .contract_schema import validate_contract
from .design_ir import validate_design_ir

def parse_object(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise ValueError(f'Duplicate JSON field: {key}')
            out[key] = value
        return out
    obj = json.loads(text, object_pairs_hook=unique)
    if not isinstance(obj, dict): raise ValueError('Expected JSON object')
    return obj

def gate_contract(contract, registry, case_id):
    validate_contract(contract, registry)
    if contract['case_id'] != case_id: raise ValueError('Contract case_id differs from requested case')
    names = {p['name'] for p in contract['module']['ports']} | {m['name'] for m in contract['models']}
    if names & {'checks','current_scenario','dut','behavior_contract_tb'}:
        raise ValueError('Name conflicts with generated testbench internals')
    checked = set(); total = 0
    def walk(steps, multiplier=1, depth=0):
        nonlocal total
        if depth > 8: raise ValueError('Contract nesting exceeds 8')
        for step in steps:
            total += multiplier
            if total > 1000000: raise ValueError('Contract exceeds execution budget')
            if step['op'] == 'expect':
                checked.update(step['values'])
                if any(re.search(r"'[bBoOhHdD][0-9a-fA-F_]*[xXzZ?]", e) for e in step['values'].values()):
                    raise ValueError('Unknown expected values are not a functional check')
            if step['op'] == 'repeat': walk(step['steps'], multiplier*step['count'], depth+1)
    for scenario in contract['scenarios']:
        before = set(checked)
        walk(scenario['steps'])
        def has_expect(steps):
            return any(s['op']=='expect' or (s['op']=='repeat' and has_expect(s['steps'])) for s in steps)
        if not has_expect(scenario['steps']): raise ValueError('Every scenario needs an executable expect')
    outputs = {p['name'] for p in contract['module']['ports'] if p['direction']=='output'}
    if not outputs or checked != outputs: raise ValueError(f'Outputs without checks: {outputs-checked}')
    for clock in contract['clocks']:
        p=next(p for p in contract['module']['ports'] if p['name']==clock['signal'])
        if p['width'] != 1 or clock['half_period'] < 2: raise ValueError('Clock must be one bit with half_period >= 2 for safe sampling')
    return contract

def gate_design(ir, contract):
    allowed={'schema_version','module','design'}
    if set(ir)!=allowed: raise ValueError('DesignIR root must be schema_version/module/design; raw RTL is forbidden')
    if set(ir['module']) != {'name','ports'}: raise ValueError('Unexpected module fields')
    permitted={'kind','signals','outputs','clock','reset','registers','transitions'}
    if set(ir['design'])-permitted: raise ValueError('Unsupported design fields')
    validate_design_ir(ir)
    def ports(module):return sorted((p['name'],p['direction'],p['width']) for p in module['ports'])
    if ports(ir['module'])!=ports(contract['module']): raise ValueError('Design and frozen contract interfaces differ')
    if ir['design']['kind']=='sequential':
        clock=ir['design']['clock']['signal']
        if clock not in {c['signal'] for c in contract['clocks']}: raise ValueError('Design clock absent from contract')
    return ir
