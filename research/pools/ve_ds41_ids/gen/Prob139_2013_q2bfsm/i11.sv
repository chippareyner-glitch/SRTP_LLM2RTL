module TopModule (
    input clk,
    input resetn,
    input x,
    input y,
    output f,
    output g
);

    typedef enum logic [3:0] {
        A, F, W, S1, S2, G1, G2, SUC, FAIL
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            A:    next_state = F;
            F:    next_state = x ? S1 : W;
            W:    next_state = x ? S1 : W;
            S1:   next_state = x ? S1 : S2;
            S2:   next_state = x ? G1 : W;
            G1:   next_state = y ? SUC : G2;
            G2:   next_state = y ? SUC : FAIL;
            SUC:  next_state = SUC;
            FAIL: next_state = FAIL;
            default: next_state = A;
        endcase
    end

    assign f = (state == F);
    assign g = (state == G1) || (state == G2) || (state == SUC);

endmodule
