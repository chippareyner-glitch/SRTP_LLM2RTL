module TopModule (
    input clk,
    input areset,
    input in,
    output reg out
);

    reg state, next;

    always @(*) begin
        case (state)
            1'b0: next = in ? 1'b0 : 1'b1;
            1'b1: next = in ? 1'b1 : 1'b0;
            default: next = 1'b1;
        endcase
    end

    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b1;
        else
            state <= next;
    end

    always @(posedge clk) begin
        out <= state;
    end

endmodule
