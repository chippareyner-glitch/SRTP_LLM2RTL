module TopModule (
  input  logic clk,
  input  logic reset,
  input  logic data,
  input  logic done_counting,
  input  logic ack,
  output logic shift_ena,
  output logic counting,
  output logic done
);

  typedef enum logic [3:0] {
    S0, S1, S2, S3,
    SHIFT1, SHIFT2, SHIFT3, SHIFT4,
    COUNT,
    DONE
  } state_t;

  state_t state, next_state;

  always_ff @(posedge clk) begin
    if (reset) state <= S0;
    else       state <= next_state;
  end

  always_comb begin
    next_state = state;
    unique case (state)
      S0: next_state = data ? S1 : S0;
      S1: next_state = data ? S2 : S0;
      S2: next_state = data ? S2 : S3;
      S3: next_state = data ? SHIFT1 : S0;
      SHIFT1: next_state = SHIFT2;
      SHIFT2: next_state = SHIFT3;
      SHIFT3: next_state = SHIFT4;
      SHIFT4: next_state = COUNT;
      COUNT: next_state = done_counting ? DONE : COUNT;
      DONE: next_state = ack ? S0 : DONE;
      default: next_state = S0;
    endcase
  end

  always_comb begin
    shift_ena = (state == SHIFT1) || (state == SHIFT2) || (state == SHIFT3) || (state == SHIFT4);
    counting  = (state == COUNT);
    done      = (state == DONE);
  end

endmodule
