module TopModule (
  input  clk,
  input  reset,
  input  data,
  input  done_counting,
  input  ack,
  output logic shift_ena,
  output logic counting,
  output logic done
);

  typedef enum logic [3:0] {
    IDLE,
    GOT1,
    GOT11,
    GOT110,
    SH1,
    SH2,
    SH3,
    SH4,
    COUNT,
    DONE
  } state_t;

  state_t state, next;

  always_ff @(posedge clk) begin
    if (reset)
      state <= IDLE;
    else
      state <= next;
  end

  always_comb begin
    next = state;
    case (state)
      IDLE:   next = data ? GOT1  : IDLE;
      GOT1:   next = data ? GOT11 : IDLE;
      GOT11:  next = data ? GOT11 : GOT110;
      GOT110: next = data ? SH1   : IDLE;
      SH1:    next = SH2;
      SH2:    next = SH3;
      SH3:    next = SH4;
      SH4:    next = COUNT;
      COUNT:  next = done_counting ? DONE : COUNT;
      DONE:   next = ack ? IDLE : DONE;
      default: next = IDLE;
    endcase
  end

  assign shift_ena = (state == SH1) || (state == SH2) ||
                     (state == SH3) || (state == SH4);
  assign counting  = (state == COUNT);
  assign done      = (state == DONE);

endmodule
