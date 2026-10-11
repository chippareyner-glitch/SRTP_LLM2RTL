module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    typedef enum logic [2:0] {
        A  = 3'd0,
        S0 = 3'd1,
        S1 = 3'd2,
        C0 = 3'd3,
        C1 = 3'd4,
        D0 = 3'd5,
        D1 = 3'd6,
        D2 = 3'd7
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
            A:  next_state = s ? S0 : A;
            S0: next_state = w ? C1 : C0;
            S1: next_state = w ? C1 : C0;
            C0: next_state = w ? D1 : D0;
            C1: next_state = w ? D2 : D1;
            D0: next_state = S0;
            D1: next_state = w ? S1 : S0;
            D2: next_state = w ? S0 : S1;
            default: next_state = A;
        endcase
    end

    assign z = (state == S1);

endmodule
