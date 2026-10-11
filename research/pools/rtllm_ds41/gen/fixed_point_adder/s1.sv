module fixed_point_adder #(
    parameter Q = 8,
    parameter N = 16
) (
    input  [N-1:0] a,
    input  [N-1:0] b,
    output [N-1:0] c
);

    localparam M = N - 1;

    reg [N-1:0] res;

    wire a_sign = a[N-1];
    wire b_sign = b[N-1];
    wire [M-1:0] a_mag = a[M-1:0];
    wire [M-1:0] b_mag = b[M-1:0];

    wire [M:0] mag_sum = {1'b0, a_mag} + {1'b0, b_mag};

    always_comb begin
        if (a_sign == b_sign) begin
            if (mag_sum[M]) begin
                res[N-1] = a_sign;
                res[M-1:0] = {M{1'b1}};
            end else begin
                res[N-1] = a_sign;
                res[M-1:0] = mag_sum[M-1:0];
            end
        end else begin
            if (a_mag > b_mag) begin
                res[N-1] = a_sign;
                res[M-1:0] = a_mag - b_mag;
            end else if (b_mag > a_mag) begin
                res[N-1] = b_sign;
                res[M-1:0] = b_mag - a_mag;
            end else begin
                res = {N{1'b0}};
            end
        end
    end

    assign c = res;

endmodule
