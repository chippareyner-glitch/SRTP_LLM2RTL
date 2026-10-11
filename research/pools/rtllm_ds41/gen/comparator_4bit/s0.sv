module comparator_4bit (
    input  logic [3:0] A,
    input  logic [3:0] B,
    output logic       A_greater,
    output logic       A_equal,
    output logic       A_less
);

    logic [4:0] diff;

    // Perform 5-bit subtraction to capture borrow
    assign diff = {1'b0, A} - {1'b0, B};

    // Borrow occurs when A < B
    assign A_less    = diff[4];
    // Equal when lower 4 bits are zero and no borrow
    assign A_equal   = (diff[3:0] == 4'b0000) && !diff[4];
    // Greater when lower 4 bits are non-zero and no borrow
    assign A_greater = (diff[3:0] != 4'b0000) && !diff[4];

endmodule
