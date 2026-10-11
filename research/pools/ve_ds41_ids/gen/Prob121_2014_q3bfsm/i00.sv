module TopModule (
  input  clk,
  input  reset,
  input  x,
  output z
);

  reg [2:0] state;
  reg [2:0] next_state;

  // Sequential state update: synchronous active-high reset to 000
  always @(posedge clk) begin
    if (reset)
      state <= 3'b000;
    else
      state <= next_state;
  end

  // Next-state combinational logic from the state-assigned table
  always @(*) begin
    case (state)
      3'b000: next_state = x ? 3'b001 : 3'b000;
      3'b001: next_state = x ? 3'b100 : 3'b001;
      3'b010: next_state = x ? 3'b001 : 3'b010;
      3'b011: next_state = x ? 3'b010 : 3'b001;
      3'b100: next_state = x ? 3'b100 : 3'b011;
      default: next_state = 3'b000;
    endcase
  end

  // Combinational Moore output: reflects current state in the same cycle
  assign z = (state == 3'b011) || (state == 3'b100);

endmodule
