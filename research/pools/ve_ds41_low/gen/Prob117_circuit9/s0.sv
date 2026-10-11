module TopModule (
  input clk,
  input a,
  output reg [2:0] q
);
  reg a_reg = 1'b1;
  always @(posedge clk) begin
    a_reg <= a;
    if (a_reg)
      q <= 3'd4;
    else
      q <= (q == 3'd6) ? 3'd0 : q + 1'b1;
  end
endmodule
