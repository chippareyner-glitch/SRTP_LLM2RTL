module comparator_4bit (
    input  logic [3:0] A,
    input  logic [3:0] B,
    output logic       A_greater,
    output logic       A_equal,
    output logic       A_less
);

    logic [4:0] diff;
    logic       borrow;

    assign diff   = {1'b0, A} - {1'b0, B};
    assign borrow = diff[4];

    always_comb begin
        A_less    = borrow;
        A_greater = ~borrow && (diff[3:0] != 4'd0);
        A_equal   = ~borrow && (diff[3:0] == 4'd0);
    end

endmodule
