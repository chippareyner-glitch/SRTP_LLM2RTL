module TopModule (
  input  clock,
  input  a,
  output p,
  output q
);

  reg p_reg;
  reg q_reg;

  // p is a level-sensitive latch enabled by clock
  always @(*) begin
    if (clock)
      p_reg = a;
  end

  // q is a flip-flop capturing p on the falling edge of clock
  always @(negedge clock) begin
    q_reg <= p_reg;
  end

  assign p = p_reg;
  assign q = q_reg;

endmodule
