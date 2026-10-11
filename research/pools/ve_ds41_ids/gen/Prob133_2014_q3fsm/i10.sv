module TopModule (
    input  clk,
    input  reset,
    input  s,
    input  w,
    output z
);

    typedef enum logic [2:0] {
        A,
        F0,
        F1,
        B1_0,
        B1_1,
        B2_0,
        B2_1,
        B2_2
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            A:    next_state = s ? F0 : A;
            F0:   next_state = w ? B1_1 : B1_0;
            F1:   next_state = w ? B1_1 : B1_0;
            B1_0: next_state = w ? B2_1 : B2_0;
            B1_1: next_state = w ? B2_2 : B2_1;
            B2_0: next_state = F0;
            B2_1: next_state = w ? F1 : F0;
            B2_2: next_state = w ? F0 : F1;
            default: next_state = A;
        endcase
    end

    assign z = (state == F1);

endmodule
