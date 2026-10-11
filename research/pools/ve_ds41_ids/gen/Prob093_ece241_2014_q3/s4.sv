module TopModule (
    input  logic c,
    input  logic d,
    output logic [3:0] mux_in
);

    assign mux_in[0] = c ? 1'b1 : d;   // f(ab=00) = c | d
    assign mux_in[1] = 1'b0;           // f(ab=01) = 0
    assign mux_in[2] = c ? d : 1'b0;   // f(ab=11) = c & d
    assign mux_in[3] = d ? c : 1'b1;   // f(ab=10) = c | ~d

endmodule
