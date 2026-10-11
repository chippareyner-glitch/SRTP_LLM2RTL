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
        COUNT, WAIT
    } state_t;

    state_t state, next;

    always_comb begin
        case (state)
            S:     next = data ? S1 : S;
            S1:    next = data ? S11 : S;
            S11:   next = data ? S11 : S110;
            S110:  next = data ? B0 : S;
            B0:    next = B1;
            B1:    next = B2;
            B2:    next = B3;
            B3:    next = COUNT;
            COUNT: next = done_counting ? WAIT : COUNT;
            WAIT:  next = ack ? S : WAIT;
            default: next = S;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) state <= S;
        else       state <= next;
    end

    assign shift_ena = (state == B0) || (state == B1) ||
                       (state == B2) || (state == B3);
    assign counting  = (state == COUNT);
    assign done      = (state == WAIT);

endmodule
