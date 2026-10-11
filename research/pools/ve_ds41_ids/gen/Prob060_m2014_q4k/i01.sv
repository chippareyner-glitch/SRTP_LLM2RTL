module TopModule (
  input  clk,
  input  resetn,
  input  in,
  output out
);

  reg [3:0] q;

  always_ff @(posedge clk) begin
    if (!resetn)
      q <= 4'b1111;          // synchronous active-low reset: all four flops set to 1
    else
      q <= {q[2:0], in};     // shift in new bit, shift existing bits toward output
  end

  assign out = q[3];

endmodule
