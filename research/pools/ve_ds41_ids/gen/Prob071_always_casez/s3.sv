module TopModule (
  input  logic [7:0] in,
  output logic [2:0] pos
);

  always_comb begin
    pos = 3'd0;
    for (int i = 7; i >= 0; i--) begin
      if (in[i])
        pos = i[2:0];
    end
  end

endmodule
