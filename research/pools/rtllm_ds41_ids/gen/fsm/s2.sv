module fsm (
    input  logic IN,
    input  logic CLK,
    input  logic RST,
    output logic MATCH
);

    typedef enum logic [2:0] {
        S0,
        S1,
        S2,
        S3,
        S4
    } state_t;

    state_t state, next_state;

    always_ff @(posedge CLK or posedge RST) begin
        if (RST)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            S0: next_state = IN ? S1 : S0;
            S1: next_state = IN ? S1 : S2;
            S2: next_state = IN ? S1 : S3;
            S3: next_state = IN ? S4 : S0;
            S4: next_state = IN ? S1 : S2;
            default: next_state = S0;
        endcase
    end

    assign MATCH = RST ? 1'b0 : (state == S4 && IN);

endmodule
