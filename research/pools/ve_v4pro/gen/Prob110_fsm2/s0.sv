module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic j,
    input  logic k,
    output logic out
);
    localparam OFF = 1'b0;
    localparam ON  = 1'b1;

    logic state;

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

    assign out = state;
endmodule
