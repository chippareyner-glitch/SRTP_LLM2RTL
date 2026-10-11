"""Spec-only semantic review, distinct from schema and constant-mutant checks."""
import json

REVIEW_SYSTEM = '''Audit an executable RTL verification contract against ONLY the original specification.
Return JSON: {"verdict":"accept|revise|uncertain", "issues":["..."], "evidence":["..."]}.
Do not treat DUT behavior as ground truth. Cite concrete source requirements and scenario steps.
Check every stimulus predicate numerically (bit indices, masks, widths); expected bytes must actually be sent.
Check independent scenarios establish initial state, including DUT reset AND model reset, or explicitly follow the preceding state.
Trace clock edges using pre-edge inputs and post-NBA outputs; wait_edge already inserts #1. Never infer another cycle from that delay.
update_model evaluates ALL right-hand sides simultaneously from OLD model values, then assigns all targets. set_model assigns sequentially. Never interpret update_model as sequential assignments.
Identify ambiguity between textual timing and example waveforms instead of silently choosing an interpretation.
For packet/serial protocols check invalid start, one full packet, two adjacent packets, and reset mid-packet when reset is specified.
Verify every data bit/byte is driven and checked in the right order, including the next packet's first byte during completion.
Check don't-care outputs are not constrained. Reject stale expected values and missing effective sampling edges.
Use uncertain for unresolved contradictions. accept requires no known semantic or coverage defect.
On repair-stall audits, separate suspect test expectations from real RTL errors; propose diagnostics, never rewrite the contract to match the DUT.'''

def parse_review(raw):
    from .gates import parse_object
    value=parse_object(raw)
    if value.get('verdict') not in {'accept','revise','uncertain'}:
        raise ValueError('Invalid semantic review verdict')
    for key in ('issues','evidence'):
        if not isinstance(value.get(key),list) or not all(isinstance(x,str) for x in value[key]):
            raise ValueError('Semantic review requires string lists')
    if value['verdict']=='accept' and value['issues']:
        raise ValueError('Accept verdict contradicts reported issues')
    if not value['evidence']:
        raise ValueError('Semantic review must provide evidence')
    return value
