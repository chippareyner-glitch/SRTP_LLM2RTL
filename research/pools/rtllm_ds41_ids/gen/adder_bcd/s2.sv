module adder_bcd (
    input  logic [3:0] A,
    input  logic [3:0] B,
    input  logic       Cin,
    output logic [3:0] Sum,
    output logic       Cout
);

    logic [4:0] binary_sum;
    logic       correction;

    always_comb begin
        binary_sum = {1'b0, A} + {1'b0, B} + {{4{1'b0}}, Cin};

        correction = (binary_sum > 5'd9);

        Cout = correction;

        if (correction)
            Sum = binary_sum[3:0] + 4'd6;
        else
            Sum = binary_sum[3:0];
    end

endmodule
