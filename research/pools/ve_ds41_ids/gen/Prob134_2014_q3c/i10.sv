module TopModule(
  input  logic       clk,
  input  logic       x,
  input  logic [2:0] y,
  output logic       Y0,
  output logic       z
);

  logic [2:0] Y_next;

  always_comb begin
    case ({x, y})
      4'b0_000: Y_next = 3'b000;
      4'b1_000: Y_next = 3'b001;
      4'b0_001: Y_next = 3'b001;
      4'b1_001: Y_next = 3'b100;
      4'b0_010: Y_next = 3'b010;
      4'b1_010: Y_next = 3'b001;
      4'b0_011: Y_next = 3'b001;
      4'b1_011: Y_next = 3'b010;
      4'b0_100: Y_next = 3'b011;
      4'b1_100: Y_next = 3'b100;
      default:  Y_next = 3'b000;
    endcase
  end

  assign Y0 = Y_next[0];
  assign z  = (y == 3'b011) || (y == 3'b100);

endmodule
