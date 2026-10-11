"""Build the seed counterfactual (CF) spec-to-RTL set from VerilogEval problems.

Each variant = original spec with a *minimal, natural* textual delta + a hand-written
reference implementing the delta.  Interfaces are unchanged, so the original official
testbench can grade a design against the CF reference (CF ref is swapped in as RefModule).

Variant categories:
  param   - a parameter of a canonical design changes (range, taps, reset value)
  rule    - a behavioural rule changes (direction, priority, edge polarity, boundary)
  name    - the behaviour changes while a canonical *name* in the interface stays (e.g. pedge)

Usage: python -I build_seed.py   -> writes variants/<id>/{prompt.txt, ref.sv, meta.json}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parents[1] / "dataset_spec-to-rtl_gcc"
OUT = HERE / "variants"


def wsre(text: str) -> re.Pattern:
    """Whitespace-insensitive literal pattern."""
    parts = [re.escape(p) for p in text.split()]
    return re.compile(r"\s+".join(parts))


RULE90_WRAP = """module RefModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);
  always @(posedge clk)
    if (load) q <= data;
    else      q <= {q[0], q[511:1]} ^ {q[510:0], q[511]};
endmodule
"""

RULE90_ONES = """module RefModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);
  always @(posedge clk)
    if (load) q <= data;
    else      q <= {1'b1, q[511:1]} ^ {q[510:0], 1'b1};
endmodule
"""

RULE110_WRAP = """module RefModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);
  wire [511:0] L = {q[0], q[511:1]};
  wire [511:0] R = {q[510:0], q[511]};
  always @(posedge clk)
    if (load) q <= data;
    else      q <= (q ^ R) | (q & ~L);
endmodule
"""

EDGE_NEG = """module RefModule (
  input clk,
  input [7:0] in,
  output reg [7:0] pedge
);
  reg [7:0] d_last;
  always @(posedge clk) begin
    d_last <= in;
    pedge <= ~in & d_last;
  end
endmodule
"""

CAPTURE_RISE = """module RefModule (
  input clk,
  input reset,
  input [31:0] in,
  output reg [31:0] out
);
  reg [31:0] d_last;
  always @(posedge clk) begin
    d_last <= in;
    if (reset) out <= '0;
    else       out <= out | (in & ~d_last);
  end
endmodule
"""

LFSR_52 = """module RefModule (
  input clk,
  input reset,
  output reg [4:0] q
);
  logic [4:0] q_next;
  always @(q) begin
    q_next = q[4:1];
    q_next[4] = q[0];
    q_next[1] ^= q[0];
  end
  always @(posedge clk)
    if (reset) q <= 5'h1;
    else       q <= q_next;
endmodule
"""

SHIFT_LEFT = """module RefModule (
  input clk,
  input areset,
  input load,
  input ena,
  input [3:0] data,
  output reg [3:0] q
);
  always @(posedge clk, posedge areset)
    if (areset)    q <= 0;
    else if (load) q <= data;
    else if (ena)  q <= {q[2:0], 1'b0};
endmodule
"""

SHIFT_ENA_PRIO = """module RefModule (
  input clk,
  input areset,
  input load,
  input ena,
  input [3:0] data,
  output reg [3:0] q
);
  always @(posedge clk, posedge areset)
    if (areset)    q <= 0;
    else if (ena)  q <= q[3:1];
    else if (load) q <= data;
endmodule
"""

SEQ_1011 = """module RefModule (
  input clk,
  input reset,
  input data,
  output start_shifting
);
  parameter S=0, S1=1, S10=2, S101=3, Done=4;
  reg [2:0] state, next;
  always_comb begin
    case (state)
      S:    next = data ? S1   : S;
      S1:   next = data ? S1   : S10;
      S10:  next = data ? S101 : S;
      S101: next = data ? Done : S10;
      Done: next = Done;
      default: next = S;
    endcase
  end
  always @(posedge clk)
    if (reset) state <= S;
    else       state <= next;
  assign start_shifting = state == Done;
endmodule
"""

SEQ_PULSE = """module RefModule (
  input clk,
  input reset,
  input data,
  output start_shifting
);
  parameter S=0, S1=1, S11=2, S110=3, Done=4;
  reg [2:0] state, next;
  always_comb begin
    case (state)
      S:    next = data ? S1   : S;
      S1:   next = data ? S11  : S;
      S11:  next = data ? S11  : S110;
      S110: next = data ? Done : S;
      Done: next = data ? S11  : S;   // suffix "1" of 1101 is a prefix: overlap allowed
      default: next = S;
    endcase
  end
  always @(posedge clk)
    if (reset) state <= S;
    else       state <= next;
  assign start_shifting = state == Done;
endmodule
"""

COUNT_3_12 = """module RefModule (
  input clk,
  input reset,
  output reg [3:0] q
);
  always @(posedge clk)
    if (reset || q == 12) q <= 3;
    else                  q <= q + 1;
endmodule
"""

COUNT_500 = """module RefModule (
  input clk,
  input reset,
  output reg [9:0] q
);
  always @(posedge clk)
    if (reset || q == 499) q <= 0;
    else                   q <= q + 1;
endmodule
"""

COUNT_DOWN = """module RefModule (
  input clk,
  input slowena,
  input reset,
  output reg [3:0] q
);
  always @(posedge clk)
    if (reset) q <= 9;
    else if (slowena) q <= (q == 0) ? 4'd9 : q - 1;
endmodule
"""

DFF_A5 = """module RefModule (
  input clk,
  input [7:0] d,
  input reset,
  output reg [7:0] q
);
  always @(posedge clk)
    if (reset) q <= 8'hA5;
    else       q <= d;
endmodule
"""

ZEROCOUNT = """module RefModule (
  input [254:0] in,
  output reg [7:0] out
);
  always_comb begin
    out = 0;
    for (int i = 0; i < 255; i++)
      out = out + !in[i];
  end
endmodule
"""

THERMO_NOFAN_HEAT = """module RefModule (
  input mode,
  input too_cold,
  input too_hot,
  input fan_on,
  output heater,
  output aircon,
  output fan
);
  assign heater = mode & too_cold;
  assign aircon = ~mode & too_hot;
  assign fan    = aircon | fan_on;
endmodule
"""

WRAP_TXT = ("The boundaries wrap around: the left neighbour of q[511] is q[0], and the right "
            "neighbour of q[0] is q[511] (a circular array).")

VARIANTS = [
    ("Prob108_rule90", "wrap", "rule", RULE90_WRAP,
     [("Assume the boundaries (q[-1] and q[512]) are both zero (off).", WRAP_TXT)]),
    ("Prob108_rule90", "ones", "rule", RULE90_ONES,
     [("Assume the boundaries (q[-1] and q[512]) are both zero (off).",
       "Assume the boundaries (q[-1] and q[512]) are both one (on).")]),
    ("Prob124_rule110", "wrap", "rule", RULE110_WRAP,
     [("Assume the boundaries (q[-1] and q[512], if they existed) are both zero (off).", WRAP_TXT)]),
    ("Prob054_edgedetect", "negedge", "name", EDGE_NEG,
     [("detect when the input signal changes from 0 in one clock cycle to 1 the next (similar to "
       "positive edge detection). The output bit should be set the cycle after a 0 to 1 transition occurs.",
       "detect when the input signal changes from 1 in one clock cycle to 0 the next (similar to "
       "negative edge detection). The output bit should be set the cycle after a 1 to 0 transition occurs.")]),
    ("Prob066_edgecapture", "rising", "rule", CAPTURE_RISE,
     [("capture when the input signal changes from 1 in one clock cycle to 0 the next.",
       "capture when the input signal changes from 0 in one clock cycle to 1 the next.")]),
    ("Prob086_lfsr5", "taps52", "param", LFSR_52,
     [("taps at bit positions 5 and 3.", "taps at bit positions 5 and 2.")]),
    ("Prob085_shift4", "left", "rule", SHIFT_LEFT,
     [("4-bit shift register (right shift)", "4-bit shift register (left shift)"),
      ("(3) ena: Shift right (q[3] becomes zero, q[0] is shifted out and disappears).",
       "(3) ena: Shift left (q[0] becomes zero, q[3] is shifted out and disappears).")]),
    ("Prob085_shift4", "enaprio", "rule", SHIFT_ENA_PRIO,
     [("If both the load and ena inputs are asserted (1), the load input has higher priority.",
       "If both the load and ena inputs are asserted (1), the ena input has higher priority "
       "(the register shifts and data is ignored).")]),
    ("Prob096_review2015_fsmseq", "seq1011", "param", SEQ_1011,
     [("searches for the sequence 1101", "searches for the sequence 1011")]),
    ("Prob096_review2015_fsmseq", "pulse", "rule", SEQ_PULSE,
     [("When the sequence is found, it should set start_shifting to 1, forever, until reset.",
       "When the sequence is found, it should set start_shifting to 1 for exactly one clock cycle "
       "and then continue searching; overlapping occurrences count (e.g. 1101101 contains two "
       "occurrences).")]),
    ("Prob035_count1to10", "3to12", "param", COUNT_3_12,
     [("decade counter that counts 1 through 10, inclusive.", "counter that counts 3 through 12, inclusive."),
      ("reset the counter to 1.", "reset the counter to 3.")]),
    ("Prob037_review2015_count1k", "500", "param", COUNT_500,
     [("counts from 0 to 999, inclusive, with a period of 1000 cycles.",
       "counts from 0 to 499, inclusive, with a period of 500 cycles.")]),
    ("Prob067_countslow", "down", "rule", COUNT_DOWN,
     [("decade counter that counts from 0 through 9, inclusive, with a period of 10.",
       "decade down-counter that counts from 9 down to 0, inclusive, with a period of 10 "
       "(after 0 it wraps back to 9)."),
      ("should reset the counter to 0.", "should reset the counter to 9."),
      ("rather than always incrementing", "rather than always decrementing"),
      ("indicates when the counter should increment", "indicates when the counter should decrement")]),
    ("Prob041_dff8r", "resetA5", "param", DFF_A5,
     [("reset setting the output to zero.", "reset setting the output to 8'hA5.")]),
    ("Prob030_popcount255", "zeros", "rule", ZEROCOUNT,
     [("A \"population count\" circuit counts the number of '1's in an input vector. The module should "
       "implement a population count circuit for a 255-bit input vector.",
       "A \"zero count\" circuit counts the number of '0's in an input vector. The module should "
       "implement a zero count circuit for a 255-bit input vector.")]),
    ("Prob072_thermostat", "nofanheat", "rule", THERMO_NOFAN_HEAT,
     [("When the heater or air conditioner are on, also turn on the fan to circulate the air.",
       "When the air conditioner is on, also turn on the fan to circulate the air; the heater is a "
       "radiant heater, so the fan should not be turned on just because the heater is on.")]),
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for base, delta, cat, ref, edits in VARIANTS:
        spec = (DATASET / f"{base}_prompt.txt").read_text(encoding="utf-8")
        new = spec
        for old, rep in edits:
            pat = wsre(old)
            if not pat.search(new):
                raise SystemExit(f"{base}/{delta}: text not found: {old[:60]}")
            new = pat.sub(lambda _m: rep, new, count=1)
        vid = f"{base}__{delta}"
        d = OUT / vid
        d.mkdir(exist_ok=True)
        (d / "prompt.txt").write_text(new, encoding="utf-8")
        (d / "ref.sv").write_text(ref, encoding="utf-8")
        (d / "meta.json").write_text(json.dumps({"id": vid, "base": base, "delta": delta, "category": cat,
                                                 "edits": edits}, indent=1), encoding="utf-8")
        print("wrote", vid)


if __name__ == "__main__":
    main()
