module adder_bcd (
    input  logic [3:0] A,
    input  logic [3:0] B,
    input  logic       Cin,
    output logic [3:0] Sum,
    output logic       Cout
);

    logic [4:0] bin_sum;
    logic [4:0] corrected_sum;

    always_comb begin
        bin_sum = {1'b0, A} + {1'b0, B} + {4'b0, Cin};

        if (bin_sum > 5'd9)
            corrected_sum = bin_sum + 5'd6;
        else
            corrected_sum = bin_sum;

        Sum  = corrected_sum[3:0];
        Cout = corrected_sum[4];
    end

endmodule
