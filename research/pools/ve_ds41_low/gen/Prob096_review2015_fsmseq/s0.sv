module TopModule (
    input  clk,
    input  reset,
    input  data,
    output logic start_shifting
);

    typedef enum logic [2:0] {
        S0,
        S1,
        S11,
        S110,
        FOUND
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0:   next_state = data ? S1 : S0;
            S1:   next_state = data ? S11 : S0;
            S11:  next_state = data ? S11 : S110;
            S110: next_state = data ? FOUND : S0;
            FOUND: next_state = FOUND;
            default: next_state = S0;
        endcase
    end

    assign start_shifting = (state == FOUND);

endmodule
