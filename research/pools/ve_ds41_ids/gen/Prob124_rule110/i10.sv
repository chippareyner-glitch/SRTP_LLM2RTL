module TopModule (
  input  logic clk,
  input  logic load,
  input  logic [511:0] data,
  output logic [511:0] q
);

  logic [511:0] next_q;
  genvar i;

  generate
    for (i = 0; i < 512; i = i + 1) begin : rule110
      logic left, center, right;
      assign left   = (i == 511) ? 1'b0 : q[i+1];
      assign center = q[i];
      assign right  = (i == 0)   ? 1'b0 : q[i-1];
      assign next_q[i] = (~left & center) | (~center & right) | (left & center & ~right);
    end
  endgenerate

  initial q = 512'b0;

  always_ff @(posedge clk) begin
    if (load)
      q <= data;
    else
      q <= next_q;
  end

endmodule
