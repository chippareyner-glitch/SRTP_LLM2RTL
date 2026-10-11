module RefModule (
  input clk,
  input reset,
  output reg [3:0] q
);
  always @(posedge clk)
    if (reset || q == 12) q <= 3;
    else                  q <= q + 1;
endmodule
