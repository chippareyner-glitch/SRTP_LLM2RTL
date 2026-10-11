module TopModule (
    input  logic c,
    input  logic d,
    output logic [3:0] mux_in
);

    // mux_in[i] is the value of the K-map column selected by {a,b}
    //   ab = 00 -> mux_in[0], ab = 01 -> mux_in[1],
    //   ab = 11 -> mux_in[2], ab = 10 -> mux_in[3]
    // as functions of c,d (implemented as 2-to-1 muxes):
    //   col 00 : 0,1,1,1 for cd = 00,01,11,10  => c | d
    //   col 01 : 0,0,0,0                        => 0
    //   col 11 : 0,0,1,0                        => c & d
    //   col 10 : 1,0,1,1                        => c | ~d
    assign mux_in[0] = d ? 1'b1 : c;    // c | d
    assign mux_in[1] = 1'b0;
    assign mux_in[2] = d ? c : 1'b0;    // c & d
    assign mux_in[3] = d ? c : 1'b1;    // c | ~d

endmodule
