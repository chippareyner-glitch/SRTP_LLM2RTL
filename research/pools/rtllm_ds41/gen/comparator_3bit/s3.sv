module comparator_3bit (
    input  logic [2:0] A,
    input  logic [2:0] B,
    output logic       A_greater,
    output logic       A_equal,
    output logic       A_less
);

    always_comb begin
        A_greater = 1'b0;
        A_equal   = 1'b0;
        A_less    = 1'b0;

        if (A > B) begin
            A_greater = 1'b1;
        end else if (A == B) begin
            A_equal = 1'b1;
        end else begin
            A_less = 1'b1;
        end
    end

endmodule
