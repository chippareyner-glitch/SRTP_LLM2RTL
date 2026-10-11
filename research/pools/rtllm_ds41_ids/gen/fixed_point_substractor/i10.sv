module fixed_point_subtractor #(
    parameter integer Q = 0,
    parameter integer N = 8
) (
    input  wire [N-1:0] a,
    input  wire [N-1:0] b,
    output wire [N-1:0] c
);

    reg [N-1:0] res;
    assign c = res;

    wire sign_a = a[N-1];
    wire [N-2:0] mag_a = a[N-2:0];
    wire sign_b = b[N-1];
    wire [N-2:0] mag_b = b[N-2:0];

    always @(*) begin
        reg [N-2:0] mag_res;
        reg sign_res;

        if (sign_a == sign_b) begin
            if (sign_a == 1'b0) begin
                // Both positive
                if (mag_a >= mag_b) begin
                    mag_res = mag_a - mag_b;
                    sign_res = 1'b0;
                end else begin
                    mag_res = mag_b - mag_a;
                    sign_res = 1'b1;
                end
            end else begin
                // Both negative
                if (mag_b >= mag_a) begin
                    mag_res = mag_b - mag_a;
                    sign_res = 1'b0;
                end else begin
                    mag_res = mag_a - mag_b;
                    sign_res = 1'b1;
                end
            end
        end else begin
            // Different signs
            mag_res = mag_a + mag_b;
            sign_res = sign_a; // If a is positive, result positive; if a negative, result negative
        end

        // Handle zero: force positive zero
        if (mag_res == 0) begin
            sign_res = 1'b0;
        end

        res = {sign_res, mag_res};
    end

endmodule
