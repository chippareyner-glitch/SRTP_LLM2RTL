module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic out
);

    typedef enum logic [1:0] {A, B, C, D} state_t;
    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = in ? B : A;
            B: next_state = in ? B : C;
            C: next_state = in ? D : A;
            D: next_state = in ? B : C;
            default: next_state = A;
        endcase
    end

    always_comb begin
        out = (state == D);
    end

endmodule
