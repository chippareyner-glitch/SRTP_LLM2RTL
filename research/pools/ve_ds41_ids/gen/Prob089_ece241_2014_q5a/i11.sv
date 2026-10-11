module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        S0 = 2'b00,
        S1 = 2'b01,
        S2 = 2'b10
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (areset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: next_state = x ? S1 : S0;
            S1: next_state = x ? S2 : S1;
            S2: next_state = x ? S2 : S1;
            default: next_state = S0;
        endcase
    end

    assign z = (state == S1);

endmodule
