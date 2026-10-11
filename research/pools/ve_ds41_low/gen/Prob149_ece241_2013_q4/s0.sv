module TopModule (
  input  logic       clk,
  input  logic       reset,
  input  logic [2:0] s,
  output logic       fr2,
  output logic       fr1,
  output logic       fr0,
  output logic       dfr
);

  logic [1:0] level_reg;
  logic       rising_reg;
  logic [1:0] level_in;

  // Decode sensor pattern into water level (0=below s0, 1=between s0/s1,
  // 2=between s1/s2, 3=above s2)
  assign level_in = {s[2], s[1] & s[0]};

  always_ff @(posedge clk) begin
    if (reset) begin
      level_reg  <= 2'd0;
      rising_reg <= 1'b0;
    end else if (level_in != level_reg) begin
      level_reg  <= level_in;
      rising_reg <= (level_in > level_reg);
    end
  end

  // Nominal flow rate outputs based on current level
  assign fr2 = (level_reg == 2'd0);
  assign fr1 = (level_reg <= 2'd1);
  assign fr0 = (level_reg <= 2'd2);

  // Supplemental flow valve: always open at lowest level, never open at
  // highest level, otherwise open only if the last sensor change was upward
  assign dfr = (level_reg == 2'd0) ? 1'b1 :
               (level_reg == 2'd3) ? 1'b0 :
               rising_reg;

endmodule
