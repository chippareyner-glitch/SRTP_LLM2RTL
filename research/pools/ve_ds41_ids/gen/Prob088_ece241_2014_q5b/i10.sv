module TopModule (
  input  wire clk,
  input  wire areset,
  input  wire x,
  output wire z
);

  localparam [1:0] A = 2'b01;
  localparam [1:0] B = 2'b10;

  reg [1:0] state;

  always @(posedge clk or posedge areset) begin
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

  assign z = (state == A) ? x : ~x;

endmodule
