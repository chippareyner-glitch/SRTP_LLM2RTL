module TopModule (
    input  logic clk,
    input  logic reset,
    output logic shift_ena
);

    typedef enum logic [2:0] {
        A, B, C, D, E
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = B;
            B: next_state = C;
            C: next_state = D;
            D: next_state = E;
            E: next_state = E;
            default: next_state = A;
        endcase
    end

    assign shift_ena = (state != E);

endmodule
