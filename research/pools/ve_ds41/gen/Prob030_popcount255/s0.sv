module TopModule (
  input  [254:0] in,
  output [7:0] out
);

  logic [255:0] bits;
  assign bits = {1'b0, in};

  logic [1:0] s1 [0:127];
  logic [2:0] s2 [0:63];
  logic [3:0] s3 [0:31];
  logic [4:0] s4 [0:15];
  logic [5:0] s5 [0:7];
  logic [6:0] s6 [0:3];
  logic [7:0] s7 [0:1];
  logic [8:0] s8;

  generate
    for (genvar i = 0; i < 128; i = i + 1) begin : L1
      assign s1[i] = bits[2*i] + bits[2*i + 1];
    end

    for (genvar i = 0; i < 64; i = i + 1) begin : L2
      assign s2[i] = s1[2*i] + s1[2*i + 1];
    end

    for (genvar i = 0; i < 32; i = i + 1) begin : L3
      assign s3[i] = s2[2*i] + s2[2*i + 1];
    end

    for (genvar i = 0; i < 16; i = i + 1) begin : L4
      assign s4[i] = s3[2*i] + s3[2*i + 1];
    end

    for (genvar i = 0; i < 8; i = i + 1) begin : L5
      assign s5[i] = s4[2*i] + s4[2*i + 1];
    end

    for (genvar i = 0; i < 4; i = i + 1) begin : L6
      assign s6[i] = s5[2*i] + s5[2*i + 1];
    end

    for (genvar i = 0; i < 2; i = i + 1) begin : L7
      assign s7[i] = s6[2*i] + s6[2*i + 1];
    end

    assign s8 = s7[0] + s7[1];
  endgenerate

  assign out = s8[7:0];

endmodule
