module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic j,
    input  logic k,
    output logic out
);

    logic state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= 1'b0;
        else begin
            case (state)
                1'b0: state <= j ? 1'b1 : 1'b0;
                1'b1: state <= k ? 1'b0 : 1'b1;
            endcase
        end
    end

    assign out = state;

endmodule
