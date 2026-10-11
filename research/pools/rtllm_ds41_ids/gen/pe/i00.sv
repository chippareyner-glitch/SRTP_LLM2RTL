module pe (
    input  logic               clk,
    input  logic               rst,
    input  logic signed [31:0] a,
    input  logic signed [31:0] b,
    output logic signed [31:0] c
);

    // Partial-sum accumulator register.
    // Asynchronous, level-sensitive reset: c is forced to 0 whenever rst is high.
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            c <= 32'sd0;
        end
        else begin
            c <= c + (a * b);
        end
    end

endmodule
