module TopModule(
  input  clk,
  input  a,
  input  b,
  output q,
  output state
);

  reg state_reg;

  initial state_reg = 1'b0;

  assign state = state_reg;
  assign q     = a ^ b ^ state_reg;

  always @(posedge clk) begin
    state_reg <= (a & b) | (state_reg & (a | b));
  end

endmodule
