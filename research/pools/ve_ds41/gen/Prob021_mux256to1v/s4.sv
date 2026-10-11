module TopModule (
    input  logic [1023:0] in,
    input  logic [7:0]    sel,
    output logic [3:0]    out
);

    wire [9:0] index = {sel, 2'b00};

    assign out = in[index +: 4];

endmodule
