module TopModule (
    input [3:1] y,
    input w,
    output Y1
);
    assign Y1 = (y == 3'b000 || y == 3'b011) ? ~w : w;
endmodule
