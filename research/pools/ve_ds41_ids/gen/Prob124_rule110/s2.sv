module TopModule (
  input  logic clk,
  input  logic load,
  input  logic [511:0] data,
  output logic [511:0] q
);

  function automatic logic rule110(input logic l, input logic c, input logic r);
    case ({l, c, r})
      3'b111: rule110 = 1'b0;
      3'b110: rule110 = 1'b1;
      3'b101: rule110 = 1'b1;
      3'b100: rule110 = 1'b0;
      3'b011: rule110 = 1'b1;
      3'b010: rule110 = 1'b1;
      3'b001: rule110 = 1'b1;
      3'b000: rule110 = 1'b0;
      default: rule110 = 1'b0;
    endcase
  endfunction

  always_ff @(posedge clk) begin
    if (load) begin
      q <= data;
    end else begin
      q[511] <= rule110(1'b0, q[511], q[510]);
      for (int i = 510; i > 0; i--) begin
        q[i] <= rule110(q[i+1], q[i], q[i-1]);
      end
      q[0] <= rule110(q[1], q[0], 1'b0);
    end
  end

endmodule
