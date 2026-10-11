module TopModule (
  input  logic clk,
  input  logic reset,
  input  logic w,
  output logic z
);

  typedef enum logic [2:0] {
    A = 3'd0,
    B = 3'd1,
    C = 3'd2,
    D = 3'd3,
    E = 3'd4,
    F = 3'd5
  } state_t;

  state_t state, next_state;

  // State table (combinational)
  always_comb begin
    next_state = state;
    case (state)
      A: next_state = w ? B : A;
      B: next_state = w ? C : D;
      C: next_state = w ? E : D;
      D: next_state = w ? F : A;
      E: next_state = w ? E : D;
      F: next_state = w ? C : D;
      default: next_state = A;
    endcase
  end

  // State flip-flops
  always_ff @(posedge clk) begin
    if (reset)
      state <= A;
    else
      state <= next_state;
  end

  // Registered output, delayed one cycle relative to the state
  always_ff @(posedge clk) begin
    if (reset)
      z <= 1'b0;
    else
      z <= (state == E) || (state == F);
  end

endmodule
