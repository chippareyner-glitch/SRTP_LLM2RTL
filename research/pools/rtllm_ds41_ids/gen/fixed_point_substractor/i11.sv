module fixed_point_subtractor #(
    parameter integer Q = 0,
    parameter integer N = 16
) (
    input  wire         clk,
    input  wire [N-1:0] a,
    input  wire [N-1:0] b,
    output wire [N-1:0] c
);

    reg [N-1:0] res;

    always @(posedge clk) begin
        res <= a - b;
    end

    assign c = res;

endmodule
