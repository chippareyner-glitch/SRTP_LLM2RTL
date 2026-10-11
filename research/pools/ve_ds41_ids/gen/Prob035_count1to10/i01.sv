module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [3:0] q
);

    initial q = 4'd1;

    always_ff @(posedge clk or posedge reset) begin
        if (reset)
            q <= 4'd1;
        else if (q == 4'd10)
            q <= 4'd1;
        else
            q <= q + 4'd1;
    end

endmodule
