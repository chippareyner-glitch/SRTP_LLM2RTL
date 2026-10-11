module TopModule (
    input clk,
    input reset,
    output reg [31:0] q
);

    wire feedback = q[0];
    wire [31:0] q_next = (q >> 1) ^ (feedback ? 32'h80200003 : 32'h00000000);

    always @(posedge clk) begin
        if (reset)
            q <= 32'h1;
        else
            q <= q_next;
    end

endmodule
