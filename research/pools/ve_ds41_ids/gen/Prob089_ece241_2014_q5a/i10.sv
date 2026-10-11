module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        A = 2'b00,
        B = 2'b01,
        C = 2'b10,
        D = 2'b11
    } state_t;

    state_t state, next;

    always_comb begin
        case (state)
            A: next = x ? B : A;
            B: next = x ? D : C;
            C: next = x ? D : C;
            D: next = x ? D : C;
            default: next = A;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else
            state <= next;
    end

    assign z = (state == B) || (state == C);

endmodule
