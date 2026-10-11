module A (
    input  wire x,
    input  wire y,
    output wire z
);
    assign z = (x ^ y) & x;
endmodule

module B (
    input  wire x,
    input  wire y,
    output wire z
);
    assign z = ~(x ^ y);
endmodule

module top (
    input  wire x,
    input  wire y,
    output wire z
);
    wire a1, b1, a2, b2;
    wire or_out, and_out;

    A u_A1 (.x(x), .y(y), .z(a1));
    B u_B1 (.x(x), .y(y), .z(b1));
    A u_A2 (.x(x), .y(y), .z(a2));
    B u_B2 (.x(x), .y(y), .z(b2));

    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;
    assign z       = or_out ^ and_out;
endmodule
