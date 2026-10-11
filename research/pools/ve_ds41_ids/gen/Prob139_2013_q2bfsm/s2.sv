module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    typedef enum logic [3:0] {
        A, B, C, D, E, F, G, H, I
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            A: next_state = B;
            B: next_state = C;
            C: next_state = x ? D : C;
            D: next_state = x ? D : E;
            E: next_state = x ? F : C;
            F: next_state = y ? H : G;
            G: next_state = y ? H : I;
            H: next_state = H;
            I: next_state = I;
            default: next_state = A;
        endcase
    end

    assign f = (state == B);
    assign g = (state == F) || (state == G) || (state == H);

endmodule
