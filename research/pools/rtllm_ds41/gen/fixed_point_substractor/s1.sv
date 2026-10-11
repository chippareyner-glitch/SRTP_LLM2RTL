module fixed_point_subtractor #(
    parameter Q = 0,
    parameter N = 8
) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] c
);

    logic [N-1:0] res;
    logic         sign_a, sign_b;
    logic [N-2:0] mag_a, mag_b;
    logic         sign_res;
    logic [N-2:0] mag_res;

    always_comb begin
        sign_a = a[N-1];
        sign_b = b[N-1];
        mag_a  = a[N-2:0];
        mag_b  = b[N-2:0];

        if (sign_a == sign_b) begin
            if (mag_a >= mag_b) begin
                mag_res  = mag_a - mag_b;
                sign_res = sign_a;
            end else begin
                mag_res  = mag_b - mag_a;
                sign_res = ~sign_a;
            end
        end else begin
            mag_res  = mag_a + mag_b;
            sign_res = sign_a;
        end

        if (mag_res == 0) begin
            sign_res = 1'b0;
        end

        res = {sign_res, mag_res};
        c   = res;
    end

endmodule
