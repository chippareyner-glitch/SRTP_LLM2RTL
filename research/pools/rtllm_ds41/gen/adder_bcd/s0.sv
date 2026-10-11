module adder_bcd (
    input  logic [3:0] A,
    input  logic [3:0] B,
    input  logic       Cin,
    output logic [3:0] Sum,
    output logic       Cout
);

    logic [4:0] sum_bin;
    logic [4:0] sum_corrected;

    always_comb begin
        sum_bin = {1'b0, A} + {1'b0, B} + Cin;

        if (sum_bin > 5'd9) begin
            sum_corrected = sum_bin + 5'd6;
            Cout = 1'b1;
        end else begin
            sum_corrected = sum_bin;
            Cout = 1'b0;
        end

        Sum = sum_corrected[3:0];
    end

endmodule
