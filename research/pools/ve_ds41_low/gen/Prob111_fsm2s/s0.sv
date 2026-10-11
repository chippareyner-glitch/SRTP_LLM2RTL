module TopModule (
  input  clk,
  input  reset,
  input  j,
  input  k,
  output out
);

  reg state; // 0 = OFF, 1 = ON

  always_ff @(posedge clk) begin
    if (reset)
      state <= 1'b0;      // synchronous active-high reset to OFF
    else if (!state)
      state <= j;         // OFF: j=0 -> OFF, j=1 -> ON
    else
      state <= ~k;        // ON : k=0 -> ON,  k=1 -> OFF
  end

  assign out = state;

endmodule
