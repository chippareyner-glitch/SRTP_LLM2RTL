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
        SF
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
        case (state)
            S0: next_state = data ? S1 : S0;
            S1: next_state = data ? S2 : S0;
            S2: next_state = data ? S2 : S3;
            S3: next_state = data ? SF : S0;
            SF: next_state = SF;
            default: next_state = S0;
        endcase
    end

    always_comb begin
        start_shifting = (state == SF) || (state == S3 && data);
    end

endmodule
