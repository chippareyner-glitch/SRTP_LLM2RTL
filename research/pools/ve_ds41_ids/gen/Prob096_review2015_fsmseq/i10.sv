module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    output logic start_shifting
);

    typedef enum logic [2:0] {
        S0,
        S1,
        S2,
        S3,
        S4
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: next_state = data ? S1 : S0;
            S1: next_state = data ? S2 : S0;
            S2: next_state = data ? S2 : S3;
            S3: next_state = data ? S4 : S0;
            S4: next_state = S4;
            default: next_state = S0;
        endcase
    end

    assign start_shifting = (state == S4);

endmodule
