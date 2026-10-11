module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic j,
    input  logic k,
    output logic out
);
    typedef enum logic {
        OFF,
        ON
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= OFF;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            OFF: next_state = j ? ON : OFF;
            ON:  next_state = k ? OFF : ON;
            default: next_state = OFF;
        endcase
    end

    assign out = (state == ON);
endmodule
