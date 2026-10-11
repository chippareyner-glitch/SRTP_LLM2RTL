module pe (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] a,
    input  logic [31:0] b,
    output logic [31:0] c
);

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            c <= 32'd0;
        end else begin
            c <= c + (a * b);
        end
    end

endmodule
