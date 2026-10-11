module A (
    input logic x,
    input logic y,
    output logic z
);
    assign z = (x ^ y) & x;
endmodule

module B (
    input logic x,
    input logic y,
    output logic z
);
    assign z = ~(x ^ y);
endmodule

module top_module (
    input logic x,
    input logic y,
    output logic z
);
    logic a1_out, a2_out;
    logic b1_out, b2_out;
    logic or_out, and_out;

    A u_A1 (
        .x (x),
        .y (y),
        .z (a1_out)
    );

    A u_A2 (
        .x (x),
        .y (y),
        .z (a2_out)
    );

    B u_B1 (
        .x (x),
        .y (y),
        .z (b1_out)
    );

    B u_B2 (
        .x (x),
        .y (y),
        .z (b2_out)
    );

    assign or_out  = a1_out | b1_out;
    assign and_out = a2_out & b2_out;
    assign z       = or_out ^ and_out;
endmodule
