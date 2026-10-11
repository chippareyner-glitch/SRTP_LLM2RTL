module fixed_point_adder #(
    parameter Q = 15,
    parameter N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;

    always_comb begin
        if (a[N-1] == b[N-1]) begin
            res[N-2:0] = a[N-2:0] + b[N-2:0];
            res[N-1]   = a[N-1];
        end else begin
            if (a[N-2:0] > b[N-2:0]) begin
                res[N-2:0] = a[N-2:0] - b[N-2:0];
                res[N-1]   = 1'b0;
            end else if (b[N-2:0] > a[N-2:0]) begin
                res[N-2:0] = b[N-2:0] - a[N-2:0];
                res[N-1]   = 1'b1;
            end else begin
                res = {N{1'b0}};
            end
        end
    end

    assign c = res;

endmodule
