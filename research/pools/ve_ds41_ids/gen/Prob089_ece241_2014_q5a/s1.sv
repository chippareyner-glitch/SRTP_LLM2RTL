module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    typedef enum logic [1:0] {
        A = 2'b00,
        B = 2'b01,
        C = 2'b10,
        D = 2'b11
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = x ? B : A;
            B: next_state = x ? D : C;
            C: next_state = x ? D : C;
            D: next_state = x ? D : C;
            default: next_state = A;
        endcase
    end

    assign z = (state == B) || (state == C);

endmodule
