module TopModule (
  input  clk,
  input  aresetn,
  input  x,
  output z
);

  typedef enum logic [1:0] {
    S0,
    S1,
    S10
  } state_t;

  state_t state, next_state;

  always_comb begin
    next_state = state;

    case (state)
      S0:  next_state = x ? S1 : S0;
      S1:  next_state = x ? S1 : S10;
      S10: next_state = x ? S1 : S0;
      default: next_state = S0;
    endcase
  end

  always_ff @(posedge clk or negedge aresetn) begin
    if (!aresetn)
      state <= S0;
    else
      state <= next_state;
  end

  assign z = (state == S10) && x;

endmodule
