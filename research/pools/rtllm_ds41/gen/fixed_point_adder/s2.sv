module fixed_point_adder #(
    parameter integer Q = 8,
    parameter integer N = 16
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;
    logic [N-2:0] mag_a;
    logic [N-2:0] mag_b;
    logic [N-1:0] mag_sum;
    logic [N-2:0] mag_diff;
    logic sign_a;
    logic sign_b;

    assign sign_a = a[N-1];
    assign sign_b = b[N-1];
    assign mag_a  = a[N-2:0];
    assign mag_b  = b[N-2:0];

    always_comb begin
        res = '0;

        if (sign_a == sign_b) begin
            mag_sum = {1'b0, mag_a} + {1'b0, mag_b};

            if (mag_sum[N-1]) begin
                // Saturate on overflow to maximum magnitude
                res = {sign_a, {N-1{1'b1}}};
            end else begin
                res = {sign_a, mag_sum[N-2:0]};
            end

            // Normalize negative zero
            if (res[N-2:0] == {N-1{1'b0}})
                res[N-1] = 1'b0;

        end else begin
            if (mag_a > mag_b) begin
                mag_diff = mag_a - mag_b;
                res = {sign_a, mag_diff};
            end else if (mag_b > mag_a) begin
                mag_diff = mag_b - mag_a;
                res = {sign_b, mag_diff};
            end else begin
                res = '0;
            end
        end
    end

    assign c = res;

endmodule
