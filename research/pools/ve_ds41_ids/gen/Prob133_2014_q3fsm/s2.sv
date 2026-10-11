module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    typedef enum logic [2:0] {
        A, B, C0, C1, D0, D1, D2
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
            z <= 1'b0;
        end else begin
            state <= next_state;
            case (state)
                A:  z <= 1'b0;
                B:  z <= 1'b0;
                C0: z <= 1'b0;
                C1: z <= 1'b0;
                D0: z <= 1'b0;
                D1: z <= w;
                D2: z <= ~w;
                default: z <= 1'b0;
            endcase
        end
    end

    always_comb begin
        case (state)
            A:  next_state = s ? B : A;
            B:  next_state = w ? C1 : C0;
            C0: next_state = w ? D1 : D0;
            C1: next_state = w ? D2 : D1;
            D0: next_state = B;
            D1: next_state = B;
            D2: next_state = B;
            default: next_state = A;
        endcase
    end

endmodule
