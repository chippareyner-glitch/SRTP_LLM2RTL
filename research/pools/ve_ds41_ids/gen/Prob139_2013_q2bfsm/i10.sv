module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    typedef enum logic [3:0] {
        A,  // reset state
        B,  // f = 1 for one cycle
        C,  // wait for first x = 1
        D,  // saw x = 1
        E,  // saw x = 1,0
        F,  // g = 1, first y check cycle
        G,  // g = 1, second y check cycle
        H,  // success: g = 1 permanently
        I   // failure: g = 0 permanently
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
