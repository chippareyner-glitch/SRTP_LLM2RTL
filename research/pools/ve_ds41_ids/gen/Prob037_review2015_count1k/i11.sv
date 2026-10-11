module TopModule (
  input  clk,
  input  reset,
  output [9:0] q
);

  reg [9:0] cnt;

  always @(posedge clk) begin
    if (reset)
      cnt <= 10'd0;
    else if (cnt == 10'd999)
      cnt <= 10'd0;
    else
      cnt <= cnt + 10'd1;
  end

  // q[0] is MSB, q[9] is LSB => output is bit-reversed counter value
  assign q = {cnt[0], cnt[1], cnt[2], cnt[3], cnt[4],
              cnt[5], cnt[6], cnt[7], cnt[8], cnt[9]};

endmodule
