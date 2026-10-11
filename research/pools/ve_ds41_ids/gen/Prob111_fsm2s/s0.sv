module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic j,
    input  logic k,
    output logic out
);

    typedef enum logic {OFF, ON} state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= OFF;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;

        case (state)
            OFF: if (j) next_state = ON;
            ON:  if (k) next_state = OFF;
        endcase
    end

    assign out = (state == ON);

endmodule
