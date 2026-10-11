module fixed_point_adder #(
    parameter int Q = 0,
    parameter int N = 8
) (
    input  logic signed [N-1:0] a,
    input  logic signed [N-1:0] b,
    output logic signed [N-1:0] c
);

    logic signed [N-1:0] res;

    always_comb begin
        res = a + b;
    end

    assign c = res;

endmodule
