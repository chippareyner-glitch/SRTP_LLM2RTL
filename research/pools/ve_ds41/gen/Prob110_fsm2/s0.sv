module TopModule (
    input  clk,
    input  areset,
    input  j,
    input  k,
    output logic out
);

    typedef enum logic {OFF, ON} state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= OFF;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            OFF: next_state = j ? ON : OFF;
            ON:  next_state = k ? OFF : ON;
            default: next_state = OFF;
        endcase
    end

    assign out = (state == ON);

endmodule
