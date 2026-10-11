module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  localparam logic [1:0] A = 2'b01;
  localparam logic [1:0] B = 2'b10;

  logic [1:0] state;
  logic [1:0] next_state;

  always_comb begin
    case (state)
      A:       next_state = x ? B : A;
      B:       next_state = B;
      default: next_state = A;
    endcase
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state <= A;
    else
      state <= next_state;
  end

  always_comb begin
    case (state)
      A:       z = x;
      B:       z = ~x;
      default: z = x;
    endcase
  end

endmodule
