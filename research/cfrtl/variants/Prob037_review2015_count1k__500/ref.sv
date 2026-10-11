module RefModule (
  input clk,
  input reset,
  output reg [9:0] q
);
  always @(posedge clk)
    if (reset || q == 499) q <= 0;
    else                   q <= q + 1;
endmodule
