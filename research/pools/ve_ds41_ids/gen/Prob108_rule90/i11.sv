module TopModule (
  input  clk,
  input  load,
  input  [511:0] data,
  output logic [511:0] q
);

  initial q = 512'b0;

  always_ff @(posedge clk) begin
    if (load)
      q <= data;
    else
      q <= {q[510:0], 1'b0} ^ {1'b0, q[511:1]};
  end

endmodule
