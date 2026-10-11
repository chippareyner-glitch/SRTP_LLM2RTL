module fixed_point_adder #(
    parameter Q = 8,
    parameter N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    localparam int MAG_BITS = N - 1;
    localparam logic [MAG_BITS-1:0] MAX_MAG = {MAG_BITS{1'b1}};

    logic [N-1:0] res;
    logic [N-1:0] sum_ext;
    logic sign_a, sign_b;
    logic [MAG_BITS-1:0] mag_a, mag_b;

    assign sign_a = a[N-1];
    assign sign_b = b[N-1];
    assign mag_a = a[MAG_BITS-1:0];
    assign mag_b = b[MAG_BITS-1:0];

    always_comb begin
        res = '0;

        if (sign_a == sign_b) begin
            // Same sign: add magnitudes
            sum_ext = {1'b0, mag_a} + {1'b0, mag_b};

            if (sum_ext[N-1]) begin
                // Overflow: saturate to maximum magnitude
                res[MAG_BITS-1:0] = MAX_MAG;
            end else begin
                res[MAG_BITS-1:0] = sum_ext[MAG_BITS-1:0];
            end

            res[N-1] = sign_a;
        end else begin
            // Different signs: subtract smaller magnitude from larger
            if (mag_a > mag_b) begin
                res[MAG_BITS-1:0] = mag_a - mag_b;
                res[N-1] = sign_a;
            end else if (mag_b > mag_a) begin
                res[MAG_BITS-1:0] = mag_b - mag_a;
                res[N-1] = sign_b;
            end else begin
                res[MAG_BITS-1:0] = '0;
                res[N-1] = 1'b0;
            end
        end
    end

    assign c = res;

endmodule
