module A (
    input  logic x,
    input  logic y,
    output logic z
);
    assign z = (x ^ y) & x;
endmodule

module B (
    input  logic x,
    input  logic y,
    output logic z
);
    assign z = ~(x ^ y);
endmodule

module top (
    input  logic x,
    input  logic y,
    output logic z
);
    logic a1, b1, a2, b2;
    logic or_out, and_out;

    A uA1 (.x(x), .y(y), .z(a1));
    B uB1 (.x(x), .y(y), .z(b1));
    A uA2 (.x(x), .y(y), .z(a2));
    B uB2 (.x(x), .y(y), .z(b2));

    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;
    assign z       = or_out ^ and_out;
endmodule
