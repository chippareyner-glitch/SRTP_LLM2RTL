module TopModule (
  input  logic clk,
  input  logic reset,
  input  logic in,
  output logic out
);

  typedef enum logic {
    A = 1'b0,
    B = 1'b1
  } state_t;

  state_t state;

  always_ff @(posedge clk) begin
    if (reset) begin
      state <= B;
    end else begin
      case (state)
        B: state <= in ? B : A;
        A: state <= in ? A : B;
        default: state <= B;
      endcase
    end
  end

  assign out = (state == B) ? 1'b1 : 1'b0;

endmodule
