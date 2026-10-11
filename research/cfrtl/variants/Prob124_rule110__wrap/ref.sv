module RefModule (
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
