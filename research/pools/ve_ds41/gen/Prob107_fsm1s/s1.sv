module TopModule (
    input  clk,
    input  reset,
    input  in,
    output out
);

    typedef enum logic {A = 1'b0, B = 1'b1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= B;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            B: next_state = in ? B : A;
            A: next_state = in ? A : B;
            default: next_state = B;
        endcase
    end

    assign out = (state == B);

endmodule
