module fixed_point_adder #(
    parameter integer Q = 8,
    parameter integer N = 16
) (
    input  wire [N-1:0] a,
    input  wire [N-1:0] b,
    output wire [N-1:0] c
);

    reg [N-1:0] res;

    always_comb begin
        res = a + b;
    end

    assign c = res;

endmodule
