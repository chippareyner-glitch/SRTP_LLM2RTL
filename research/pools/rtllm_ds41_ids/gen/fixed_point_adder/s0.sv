module fixed_point_adder #(
    parameter integer Q = 8,
    parameter integer N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;
    logic [N:0]   sum_ext;

    always_comb begin
        sum_ext = {a[N-1], a} + {b[N-1], b};

        if (a[N-1] == b[N-1] && sum_ext[N-1] != a[N-1]) begin
            // Overflow: saturate
            if (a[N-1] == 1'b0) begin
                res = {1'b0, {N-1{1'b1}}};  // Max positive
            end else begin
                res = {1'b1, {N-1{1'b0}}};  // Min negative
            end
        end else begin
            res = sum_ext[N-1:0];
        end
    end

    assign c = res;

endmodule
