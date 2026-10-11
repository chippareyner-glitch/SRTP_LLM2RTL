module TopModule (
  input  logic         clk,
  input  logic         load,
  input  logic [511:0] data,
  output logic [511:0] q
);

  logic [511:0] next_q;

  function automatic logic rule110(
    input logic left,
    input logic center,
    input logic right
  );
    case ({left, center, right})
      3'b111: rule110 = 1'b0;
      3'b110: rule110 = 1'b1;
      3'b101: rule110 = 1'b1;
      3'b100: rule110 = 1'b0;
      3'b011: rule110 = 1'b1;
      3'b010: rule110 = 1'b1;
      3'b001: rule110 = 1'b1;
      default: rule110 = 1'b0;
    endcase
  endfunction

  always_comb begin
    for (int i = 0; i < 512; i++) begin
      logic left, center, right;
      left   = (i == 511) ? 1'b0 : q[i+1];
      center = q[i];
      right  = (i == 0)   ? 1'b0 : q[i-1];
      next_q[i] = rule110(left, center, right);
    end
  end

  always_ff @(posedge clk) begin
    if (load)
      q <= data;
    else
      q <= next_q;
  end

endmodule
