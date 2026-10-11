module adder_bcd (
    input  logic [3:0] A,
    input  logic [3:0] B,
    input  logic       Cin,
    output logic [3:0] Sum,
    output logic       Cout
);

    logic [4:0] binary_sum;
    logic [4:0] bcd_corrected;

    always_comb begin
        binary_sum = {1'b0, A} + {1'b0, B} + {{4{1'b0}}, Cin};

        if (binary_sum > 5'd9) begin
            bcd_corrected = binary_sum + 5'd6;
            Cout = 1'b1;
        end else begin
            bcd_corrected = binary_sum;
            Cout = 1'b0;
        end

        Sum = bcd_corrected[3:0];
    end

endmodule
