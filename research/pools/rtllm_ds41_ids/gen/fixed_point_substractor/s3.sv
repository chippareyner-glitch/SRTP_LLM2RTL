module fixed_point_subtractor #(
    parameter Q = 8,
    parameter N = 16
)(
    input  [N-1:0] a,
    input  [N-1:0] b,
    output [N-1:0] c
);

    reg [N-1:0] res;

    wire sign_a = a[N-1];
    wire [N-2:0] mag_a = a[N-2:0];
    wire sign_b = b[N-1];
    wire [N-2:0] mag_b = b[N-2:0];

    reg sign_c;
    reg [N-2:0] mag_c;

    always_comb begin
        if (sign_a == sign_b) begin
            if (mag_a >= mag_b) begin
                sign_c = sign_a;
                mag_c = mag_a - mag_b;
            end else begin
                sign_c = ~sign_a;
                mag_c = mag_b - mag_a;
            end
        end else begin
            sign_c = sign_a;
            mag_c = mag_a + mag_b;
        end
        if (mag_c == 0) begin
            sign_c = 1'b0;
        end
        res = {sign_c, mag_c};
    end

    assign c = res;

endmodule
