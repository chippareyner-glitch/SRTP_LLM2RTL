module TopModule (
  input  logic       clk,
  input  logic       reset,
  output logic [0:3] q
);

  logic [3:0] cnt;

  always_ff @(posedge clk) begin
    if (reset)
      cnt <= 4'd0;
    else if (cnt == 4'd9)
      cnt <= 4'd0;
    else
      cnt <= cnt + 1'b1;
  end

  assign q = {cnt[0], cnt[1], cnt[2], cnt[3]};

endmodule
