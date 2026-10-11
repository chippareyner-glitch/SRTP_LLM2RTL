module TopModule (
  input  wire       clk,
  input  wire [7:0] d,
  output logic [7:0] q
);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
