module fixed_point_adder #(
    parameter Q = 8,
    parameter N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;
    logic [N-1:0] sum;
    logic overflow;

    assign sum = a + b;
    assign overflow = (a[N-1] == b[N-1]) && (sum[N-1] != a[N-1]);

    always_comb begin
        if (overflow) begin
            if (a[N-1] == 1'b0) begin
                res = {1'b0, {(N-1){1'b1}}}; // Max positive
            end else begin
                res = {1'b1, {(N-1){1'b0}}}; // Max negative
            end
        end else begin
            res = sum;
        end
    end

    assign c = res;

endmodule
