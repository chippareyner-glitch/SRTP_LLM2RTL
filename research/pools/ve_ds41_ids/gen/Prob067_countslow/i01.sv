module TopModule (
  input  clk,
  input  reset,
  input  slowena,
  output logic [3:0] q
);

  always_ff @(posedge clk) begin
    if (slowena) begin
      if (q == 4'd9)
        q <= 4'd0;
      else
        q <= q + 4'd1;
    end
    else if (reset) begin
      q <= 4'd0;
    end
  end

endmodule
