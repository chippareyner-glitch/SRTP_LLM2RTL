module fixed_point_adder #(
    parameter Q = 8,
    parameter N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;
    logic [N-1:0] mag_sum;

    always_comb begin
        if (a[N-1] == b[N-1]) begin
            // Same sign: add absolute values, keep sign
            mag_sum = {1'b0, a[N-2:0]} + {1'b0, b[N-2:0]};
            res[N-1] = a[N-1];
            if (mag_sum[N-1]) begin
                // Overflow: saturate to maximum magnitude
                res[N-2:0] = {N-1{1'b1}};
            end else begin
                res[N-2:0] = mag_sum[N-2:0];
            end
        end else begin
            // Different signs: subtract smaller magnitude from larger
            if (a[N-2:0] > b[N-2:0]) begin
                res[N-1] = a[N-1];
                res[N-2:0] = a[N-2:0] - b[N-2:0];
            end else if (b[N-2:0] > a[N-2:0]) begin
                res[N-1] = b[N-1];
                res[N-2:0] = b[N-2:0] - a[N-2:0];
            end else begin
                // Magnitudes equal: result is zero
                res[N-1] = 1'b0;
                res[N-2:0] = {N-1{1'b0}};
            end
        end
    end

    assign c = res;

endmodule
