module RefModule (
  input clk,
  input slowena,
  input reset,
  output reg [3:0] q
);
  always @(posedge clk)
    if (reset) q <= 9;
    else if (slowena) q <= (q == 0) ? 4'd9 : q - 1;
endmodule
