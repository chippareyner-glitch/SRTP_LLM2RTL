module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  localparam [1:0] A = 2'b01;
  localparam [1:0] B = 2'b10;

  logic [1:0] state;

  always_ff @(posedge clk) begin
    if (areset) begin
      state <= A;
    end else begin
      case (state)
        A: state <= x ? B : A;
        B: state <= B;
        default: state <= A;
      endcase
    end
  end

  always_comb begin
    case (state)
      A: z = x;
      B: z = ~x;
      default: z = x;
    endcase
  end

endmodule
