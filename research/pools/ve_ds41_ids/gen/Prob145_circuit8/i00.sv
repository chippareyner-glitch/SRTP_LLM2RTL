module TopModule (
  input  clock,
  input  a,
  output logic p,
  output logic q
);

  always_latch begin
    if (clock) p <= a;
  end

  always_latch begin
    if (!clock) q <= p;
  end

endmodule
