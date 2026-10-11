module TopModule (
    input  logic a,
    input  logic b,
    input  logic c,
    input  logic d,
    output logic q
);
    always_comb begin
        if ((a === 1'bx) || (b === 1'bx) || (c === 1'bx) || (d === 1'bx))
            q = 1'bx;
        else
            q = (a | b) & (c | d);
    end
endmodule
