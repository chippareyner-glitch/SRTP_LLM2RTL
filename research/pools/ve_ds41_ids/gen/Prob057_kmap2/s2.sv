module TopModule (
    input  logic a,
    input  logic b,
    input  logic c,
    input  logic d,
    output logic out
);

    assign out = (~b & ~c) | (~a & ~d) | (b & c & d) | (a & c & d);

endmodule
