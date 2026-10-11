module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic w,
    output logic z
);

    typedef enum logic [2:0] {
        A = 3'd0,
        B = 3'd1,
        C = 3'd2,
        D = 3'd3,
        E = 3'd4,
        F = 3'd5
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            A: next_state = w ? A : B;
            B: next_state = w ? D : C;
            C: next_state = w ? D : E;
            D: next_state = w ? A : F;
            E: next_state = w ? D : E;
            F: next_state = w ? D : C;
            default: next_state = A;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
        end else begin
            state <= next_state;
        end
    end

    assign z = (state == E) || (state == F);

endmodule
