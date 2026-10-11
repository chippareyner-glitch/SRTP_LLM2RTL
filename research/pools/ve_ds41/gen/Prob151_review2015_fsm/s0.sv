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
        S, S1, S11, S110,
        SHIFT1, SHIFT2, SHIFT3, SHIFT4,
        COUNT, DONE
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= S;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S:      next_state = data ? S1 : S;
            S1:     next_state = data ? S11 : S;
            S11:    next_state = data ? S11 : S110;
            S110:   next_state = data ? SHIFT1 : S;
            SHIFT1: next_state = SHIFT2;
            SHIFT2: next_state = SHIFT3;
            SHIFT3: next_state = SHIFT4;
            SHIFT4: next_state = COUNT;
            COUNT:  next_state = done_counting ? DONE : COUNT;
            DONE:   next_state = ack ? S : DONE;
            default: next_state = S;
        endcase
    end

    assign shift_ena = (state == SHIFT1) || (state == SHIFT2) ||
                       (state == SHIFT3) || (state == SHIFT4);
    assign counting  = (state == COUNT);
    assign done      = (state == DONE);

endmodule
