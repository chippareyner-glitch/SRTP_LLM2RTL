module TopModule (
    input  logic clk,
    input  logic aresetn,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        S0 = 2'b00, // no useful prefix
        S1 = 2'b01, // seen "1"
        S2 = 2'b10  // seen "10"
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or negedge aresetn) begin
        if (!aresetn)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;

        case (state)
            S0: next_state = x ? S1 : S0;
            S1: next_state = x ? S1 : S2;
            S2: next_state = x ? S1 : S0;
            default: next_state = S0;
        endcase
    end

    assign z = (state == S2) && x;

endmodule
