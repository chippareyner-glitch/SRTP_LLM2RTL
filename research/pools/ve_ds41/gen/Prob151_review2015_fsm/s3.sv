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
        S, S1, S11, S110,
        B0, B1, B2, B3,
        COUNT, DONE
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            S:      next_state = data ? S1 : S;
            S1:     next_state = data ? S11 : S;
            S11:    next_state = data ? S11 : S110;
            S110:   next_state = data ? B0 : S;
            B0:     next_state = B1;
            B1:     next_state = B2;
            B2:     next_state = B3;
            B3:     next_state = COUNT;
            COUNT:  next_state = done_counting ? DONE : COUNT;
            DONE:   next_state = ack ? S : DONE;
            default: next_state = S;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) state <= S;
        else       state <= next_state;
    end

    assign shift_ena = (state == B0) || (state == B1) || (state == B2) || (state == B3);
    assign counting  = (state == COUNT);
    assign done      = (state == DONE);

endmodule
