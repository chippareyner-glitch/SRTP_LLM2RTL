module adder_bcd (
    input  logic [3:0] A,
    input  logic [3:0] B,
    input  logic       Cin,
    output logic [3:0] Sum,
    output logic       Cout
);

    logic [4:0] temp;
    logic [4:0] corrected;

    assign temp = {1'b0, A} + {1'b0, B} + Cin;
    assign corrected = temp + 5'd6;
    assign {Cout, Sum} = (temp > 5'd9) ? corrected : temp;

endmodule
