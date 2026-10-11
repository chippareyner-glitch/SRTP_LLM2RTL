module TopModule (
    input  clk,
    input  reset,
    output logic [4:0] q
);

    // 5-bit maximal-length Galois LFSR, taps at bit positions 5 and 3
    // (position 5 = q[4], position 3 = q[2]).
    // Shifts right; tapped bits are XORed with the LSB output q[0].
    localparam logic [4:0] TAPS = 5'b10100;

    always_ff @(posedge clk) begin
        if (reset)
            q <= 5'b00001;
        else
            q <= (q >> 1) ^ (q[0] ? TAPS : 5'b00000);
    end

endmodule
