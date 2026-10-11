module fixed_point_subtractor #(
    parameter integer Q = 8,
    parameter integer N = 16
) (
    input  wire [N-1:0] a,
    input  wire [N-1:0] b,
    output wire [N-1:0] c
);

    reg [N-2:0] mag_a;
    reg [N-2:0] mag_b;
    reg [N-2:0] mag_c;
    reg         sign_a;
    reg         sign_b;
    reg         sign_c;
    reg [N-1:0] res;

    always @* begin
        sign_a = a[N-1];
        sign_b = b[N-1];
        mag_a  = a[N-2:0];
        mag_b  = b[N-2:0];

        if (sign_a == sign_b) begin
            if (mag_a >= mag_b) begin
                mag_c  = mag_a - mag_b;
                sign_c = sign_a;
            end else begin
                mag_c  = mag_b - mag_a;
                sign_c = ~sign_a;
            end
        end else begin
            mag_c  = mag_a + mag_b;
            sign_c = sign_a;
        end

        if (mag_c == 0) begin
            sign_c = 1'b0;
        end

        res = {sign_c, mag_c};
    end

    assign c = res;

endmodule
