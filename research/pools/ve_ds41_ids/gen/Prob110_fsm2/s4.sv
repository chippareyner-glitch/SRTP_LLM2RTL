module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic j,
    input  logic k,
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
            OFF: begin
                if (j)
                    next_state = ON;
                else
                    next_state = OFF;
            end

            ON: begin
                if (k)
                    next_state = OFF;
                else
                    next_state = ON;
            end

            default: next_state = OFF;
        endcase
    end

    assign out = (state == ON);

endmodule
