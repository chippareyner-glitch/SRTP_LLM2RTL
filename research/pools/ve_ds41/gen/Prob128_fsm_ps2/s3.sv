module TopModule (
    input clk,
    input reset,
    input [7:0] in,
    output done
);

    typedef enum logic [1:0] {
        A = 2'b00,
        B = 2'b01,
        C = 2'b10,
        D = 2'b11
    } state_t;

    state_t state, next_state;

    always @(*) begin
        case (state)
            A: next_state = in[3] ? B : A;
            B: next_state = C;
            C: next_state = D;
            D: next_state = in[3] ? B : A;
            default: next_state = A;
        endcase
    end

    always @(posedge clk) begin
        if (reset)
            state <= A;
        else
            state <= next_state;
    end

    assign done = (state == D);

endmodule
