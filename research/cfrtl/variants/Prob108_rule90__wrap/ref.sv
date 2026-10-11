module RefModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);
  always @(posedge clk)
    if (load) q <= data;
    else      q <= {q[0], q[511:1]} ^ {q[510:0], q[511]};
endmodule
