module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [31:0] q
);

    always_ff @(posedge clk) begin
        if (reset)
            q <= 32'h1;
        else if (q[0])
            q <= (q >> 1) ^ 32'h80200003;
        else
            q <= (q >> 1);
    end

endmodule
