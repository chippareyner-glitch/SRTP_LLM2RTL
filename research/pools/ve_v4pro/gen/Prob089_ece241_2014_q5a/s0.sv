module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        S0_NO_ONE   = 2'b00, // no 1 seen yet
        S1_ONE_OUT1 = 2'b01, // first 1 seen, current output is 1
        S2_ONE_OUT0 = 2'b10  // first 1 seen, current output is 0
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= S0_NO_ONE;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = S0_NO_ONE;
        case (state)
            S0_NO_ONE:   next_state = x ? S1_ONE_OUT1 : S0_NO_ONE;
            S1_ONE_OUT1: next_state = x ? S2_ONE_OUT0 : S1_ONE_OUT1;
            S2_ONE_OUT0: next_state = x ? S2_ONE_OUT0 : S1_ONE_OUT1;
            default:      next_state = S0_NO_ONE;
        endcase
    end

    assign z = (state == S1_ONE_OUT1);

endmodule
