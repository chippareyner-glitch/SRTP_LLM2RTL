module TopModule (
  input  clk,
  input  a,
  output reg q
);

  reg d;

  initial begin
    d = 0;
    q = 0;
  end

  always @(posedge clk) begin
    d <= a;
    q <= ~d;
  end

endmodule
