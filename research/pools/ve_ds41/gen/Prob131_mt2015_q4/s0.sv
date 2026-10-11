module A(
    input  x,
    input  y,
    output z
);
    assign z = (x ^ y) & x;
endmodule

module B(
    input  x,
    input  y,
    output z
);
    assign z = ~(x ^ y);
endmodule

module top(
    input  x,
    input  y,
    output z
);
    wire a1, b1, a2, b2;
    wire or_out, and_out;

    A uA1 (
        .x(x),
        .y(y),
        .z(a1)
    );

    B uB1 (
        .x(x),
        .y(y),
        .z(b1)
    );

    A uA2 (
        .x(x),
        .y(y),
        .z(a2)
    );

    B uB2 (
        .x(x),
        .y(y),
        .z(b2)
    );

    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;
    assign z       = or_out ^ and_out;
endmodule
