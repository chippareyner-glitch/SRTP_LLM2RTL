module mux2X1 (
    input  logic a,
    input  logic b,
    input  logic sel,
    output logic y
);
    assign y = sel ? b : a;
endmodule

module barrel_shifter (
    input  logic [7:0] in,
    input  logic [2:0] ctrl,
    output logic [7:0] out
);

    logic [7:0] stage1;
    logic [7:0] stage2;
    logic [7:0] stage3;

    // Stage 1: shift right by 4 when ctrl[2] == 1
    mux2X1 m0  (.a(in[0]),      .b(in[4]),      .sel(ctrl[2]), .y(stage1[0]));
    mux2X1 m1  (.a(in[1]),      .b(in[5]),      .sel(ctrl[2]), .y(stage1[1]));
    mux2X1 m2  (.a(in[2]),      .b(in[6]),      .sel(ctrl[2]), .y(stage1[2]));
    mux2X1 m3  (.a(in[3]),      .b(in[7]),      .sel(ctrl[2]), .y(stage1[3]));
    mux2X1 m4  (.a(in[4]),      .b(1'b0),       .sel(ctrl[2]), .y(stage1[4]));
    mux2X1 m5  (.a(in[5]),      .b(1'b0),       .sel(ctrl[2]), .y(stage1[5]));
    mux2X1 m6  (.a(in[6]),      .b(1'b0),       .sel(ctrl[2]), .y(stage1[6]));
    mux2X1 m7  (.a(in[7]),      .b(1'b0),       .sel(ctrl[2]), .y(stage1[7]));

    // Stage 2: shift right by 2 when ctrl[1] == 1
    mux2X1 m8  (.a(stage1[0]),  .b(stage1[2]),  .sel(ctrl[1]), .y(stage2[0]));
    mux2X1 m9  (.a(stage1[1]),  .b(stage1[3]),  .sel(ctrl[1]), .y(stage2[1]));
    mux2X1 m10 (.a(stage1[2]),  .b(stage1[4]),  .sel(ctrl[1]), .y(stage2[2]));
    mux2X1 m11 (.a(stage1[3]),  .b(stage1[5]),  .sel(ctrl[1]), .y(stage2[3]));
    mux2X1 m12 (.a(stage1[4]),  .b(stage1[6]),  .sel(ctrl[1]), .y(stage2[4]));
    mux2X1 m13 (.a(stage1[5]),  .b(stage1[7]),  .sel(ctrl[1]), .y(stage2[5]));
    mux2X1 m14 (.a(stage1[6]),  .b(1'b0),       .sel(ctrl[1]), .y(stage2[6]));
    mux2X1 m15 (.a(stage1[7]),  .b(1'b0),       .sel(ctrl[1]), .y(stage2[7]));

    // Stage 3: shift right by 1 when ctrl[0] == 1
    mux2X1 m16 (.a(stage2[0]),  .b(stage2[1]),  .sel(ctrl[0]), .y(stage3[0]));
    mux2X1 m17 (.a(stage2[1]),  .b(stage2[2]),  .sel(ctrl[0]), .y(stage3[1]));
    mux2X1 m18 (.a(stage2[2]),  .b(stage2[3]),  .sel(ctrl[0]), .y(stage3[2]));
    mux2X1 m19 (.a(stage2[3]),  .b(stage2[4]),  .sel(ctrl[0]), .y(stage3[3]));
    mux2X1 m20 (.a(stage2[4]),  .b(stage2[5]),  .sel(ctrl[0]), .y(stage3[4]));
    mux2X1 m21 (.a(stage2[5]),  .b(stage2[6]),  .sel(ctrl[0]), .y(stage3[5]));
    mux2X1 m22 (.a(stage2[6]),  .b(stage2[7]),  .sel(ctrl[0]), .y(stage3[6]));
    mux2X1 m23 (.a(stage2[7]),  .b(1'b0),       .sel(ctrl[0]), .y(stage3[7]));

    assign out = stage3;

endmodule
