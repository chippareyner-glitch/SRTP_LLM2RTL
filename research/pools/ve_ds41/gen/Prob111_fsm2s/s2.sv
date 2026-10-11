module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic j,
    input  logic k,
    output logic out
);

    typedef enum logic {OFF = 1'b0, ON = 1'b1} state_t;
    state_t state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= OFF;
        end else begin
            case (state)
                OFF: begin
                    if (j)
                        state <= ON;
                    else
                        state <= OFF;
                end
                ON: begin
                    if (k)
                        state <= OFF;
                    else
                        state <= ON;
                end
                default: state <= OFF;
            endcase
        end
    end

    assign out = (state == ON);

endmodule
