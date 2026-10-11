module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic j,
    input  logic k,
    output logic out
);

    typedef enum logic {OFF, ON} state_t;
    state_t state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= OFF;
        end else begin
            case (state)
                OFF: state <= j ? ON : OFF;
                ON:  state <= k ? OFF : ON;
                default: state <= OFF;
            endcase
        end
    end

    assign out = (state == ON);

endmodule
