module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic out
);
    typedef enum logic [0:0] {
        B = 1'b0,
        A = 1'b1
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            B: next_state = (in == 1'b1) ? B : A;
            A: next_state = (in == 1'b1) ? A : B;
            default: next_state = B;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= B;
        else
            state <= next_state;
    end

    assign out = (state == B) ? 1'b1 : 1'b0;
endmodule
