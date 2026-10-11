module TopModule (
  input  clk,
  input  reset,
  input  [31:0] in,
  output logic [31:0] out
);

  logic [31:0] prev;

  always_ff @(posedge clk) begin
    if (reset) begin
      prev <= 32'b0;
      out  <= 32'b0;
    end else begin
      for (int i = 0; i < 32; i++) begin
        if (prev[i] && !in[i])
          out[i] <= 1'b1;
        else
          out[i] <= out[i];
      end
      prev <= in;
    end
  end

endmodule
