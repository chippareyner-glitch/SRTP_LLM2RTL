module TopModule (
    input  a,
    input  b,
    output out_assign,
    output out_alwaysblock
);

    // AND gate using continuous assignment
    assign out_assign = a & b;

    // AND gate using combinational always block
    always_comb begin
        out_alwaysblock = a & b;
    end

endmodule
