module TopModule (
  input  logic        clk,
  input  logic        reset,
  output logic [31:0] q
);

  // Galois LFSR, right shift, taps at bit positions 32, 22, 2, 1
  // (i.e. indices 31, 21, 1, 0). Each tapped bit is XORed with q[0].
  always_ff @(posedge clk) begin
    if (reset)
      q <= 32'h0000_0001;
    else
      q <= (q >> 1) ^ (q[0] ? 32'h8020_0003 : 32'h0000_0000);
  end

endmodule
