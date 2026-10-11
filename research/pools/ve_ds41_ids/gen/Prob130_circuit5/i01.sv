module TopModule(
  input  logic [3:0] a,
  input  logic [3:0] b,
  input  logic [3:0] c,
  input  logic [3:0] d,
  input  logic [3:0] e,
  output logic [3:0] q
);

  always_comb begin
    case (c)
      4'h0: q = 4'hB;
      4'h1: q = 4'hE;
      4'h2: q = 4'hA;
      4'h3: q = 4'hD;
      default: q = 4'hF;
    endcase
  end

endmodule
