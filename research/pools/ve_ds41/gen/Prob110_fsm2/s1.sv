module TopModule (
    input  clk,
    input  areset,
    input  j,
    input  k,
    output out
);

    logic state;

    localparam logic OFF = 1'b0;
    localparam logic ON  = 1'b1;

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
