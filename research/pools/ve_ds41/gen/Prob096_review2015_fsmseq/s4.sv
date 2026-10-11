module TopModule (
  input  logic clk,
  input  logic reset,
  input  logic data,
  output logic start_shifting
);

  typedef enum logic [2:0] {
    A, // wait for 1
    B, // got 1
    C, // got 11
    D, // got 110
    E  // got 1101, start_shifting stays 1
  } state_t;

  state_t state, next_state;

  always_ff @(posedge clk) begin
    if (reset) begin
      state <= A;
      start_shifting <= 1'b0;
    end else begin
      state <= next_state;
      start_shifting <= (next_state == E);
    end
  end

  always_comb begin
    next_state = state;
    case (state)
      A: next_state = data ? B : A;
      B: next_state = data ? C : A;
      C: next_state = data ? C : D;
      D: next_state = data ? E : A;
      E: next_state = E;
      default: next_state = A;
    endcase
  end

endmodule
