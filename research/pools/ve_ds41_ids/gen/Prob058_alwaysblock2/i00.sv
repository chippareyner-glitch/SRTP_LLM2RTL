module TopModule (
  input  clk,
  input  a,
  input  b,
  output logic out_assign,
  output logic out_always_comb,
  output logic out_always_ff
);

  // XOR implemented with a continuous assignment
  assign out_assign = a ^ b;

  // XOR implemented with a combinational always block
  always @(*) begin
    out_always_comb = a ^ b;
  end

  // XOR implemented with a clocked always block (flip-flop, delayed by one cycle)
  // No reset: out_always_ff is X until the first posedge clk
  always @(posedge clk) begin
    out_always_ff <= a ^ b;
  end

endmodule
