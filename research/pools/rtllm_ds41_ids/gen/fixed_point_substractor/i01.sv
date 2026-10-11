module fixed_point_subtractor #(
    parameter Q = 8,   // number of fractional bits (fixed-point precision)
    parameter N = 16   // total word width (sign bit + magnitude bits)
)(
    input  logic [N-1:0] a,   // sign-magnitude fixed-point operand: {sign, magnitude}
    input  logic [N-1:0] b,   // sign-magnitude fixed-point operand: {sign, magnitude}
    output logic [N-1:0] c    // sign-magnitude fixed-point difference: {sign, magnitude}
);

    // Internal result variable ("register" holding the computed difference)
    logic [N-1:0] res;

    // Field extraction: MSB is an independent sign bit, remaining bits are magnitude
    logic        sign_a, sign_b, sign_res;
    logic [N-2:0] mag_a, mag_b, mag_res;

    // Extended-width magnitude sum used by the different-sign (add) case
    logic [N-1:0] mag_sum;

    assign sign_a = a[N-1];
    assign sign_b = b[N-1];
    assign mag_a  = a[N-2:0];
    assign mag_b  = b[N-2:0];

    always_comb begin
        // Defaults
        sign_res = 1'b0;
        mag_res  = '0;
        mag_sum  = '0;

        if (sign_a == sign_b) begin
            // ---- Same sign: subtract magnitudes, keep the common sign ----
            if (mag_a >= mag_b) begin
                mag_res  = mag_a - mag_b;
                sign_res = sign_a;
            end else begin
                mag_res  = mag_b - mag_a;
                sign_res = ~sign_a;
            end
        end else begin
            // ---- Different signs: add magnitudes ----
            // a - b with opposite signs is an addition of the magnitudes;
            // the sign of the result follows the sign of a.
            mag_sum  = {1'b0, mag_a} + {1'b0, mag_b};
            mag_res  = mag_sum[N-2:0];
            sign_res = sign_a;
        end

        // ---- Zero handling: force sign bit to 0 when magnitude is zero ----
        if (mag_res == '0)
            sign_res = 1'b0;

        res = {sign_res, mag_res};
    end

    assign c = res;

endmodule
