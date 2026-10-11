module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [31:0] q
);

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 32'h1;
        end else begin
            q <= (q >> 1) ^ ({32{q[0]}} & 32'h80400006);
        end
    end

endmodule
