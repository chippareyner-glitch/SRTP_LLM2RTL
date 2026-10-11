module TopModule (
    input  logic signed [7:0] a,
    input  logic signed [7:0] b,
    output logic signed [7:0] s,
    output logic overflow
);

    logic signed [8:0] a_ext;
    logic signed [8:0] b_ext;
    logic signed [8:0] sum_ext;

    always_comb begin
        a_ext = {a[7], a};
        b_ext = {b[7], b};
        sum_ext = a_ext + b_ext;
        s = sum_ext[7:0];
        overflow = sum_ext[8] ^ sum_ext[7];
    end

endmodule
