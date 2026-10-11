module mux2X1 (
    input  wire a,
    input  wire b,
    input  wire sel,
    output wire y
);
    assign y = sel ? b : a;
endmodule

module barrel_shifter (
    input  wire [7:0] in,
    input  wire [2:0] ctrl,
    output wire [7:0] out
);

    wire [7:0] stage1;
    wire [7:0] stage2;
    wire [7:0] stage3;

    // Stage 1: shift right by 4 when ctrl[2] is high
    mux2X1 s1_0 (.a(in[0]), .b(in[4]), .sel(ctrl[2]), .y(stage1[0]));
    mux2X1 s1_1 (.a(in[1]), .b(in[5]), .sel(ctrl[2]), .y(stage1[1]));
    mux2X1 s1_2 (.a(in[2]), .b(in[6]), .sel(ctrl[2]), .y(stage1[2]));
    mux2X1 s1_3 (.a(in[3]), .b(in[7]), .sel(ctrl[2]), .y(stage1[3]));
    mux2X1 s1_4 (.a(in[4]), .b(1'b0), .sel(ctrl[2]), .y(stage1[4]));
    mux2X1 s1_5 (.a(in[5]), .b(1'b0), .sel(ctrl[2]), .y(stage1[5]));
    mux2X1 s1_6 (.a(in[6]), .b(1'b0), .sel(ctrl[2]), .y(stage1[6]));
    mux2X1 s1_7 (.a(in[7]), .b(1'b0), .sel(ctrl[2]), .y(stage1[7]));

    // Stage 2: shift right by 2 when ctrl[1] is high
    mux2X1 s2_0 (.a(stage1[0]), .b(stage1[2]), .sel(ctrl[1]), .y(stage2[0]));
    mux2X1 s2_1 (.a(stage1[1]), .b(stage1[3]), .sel(ctrl[1]), .y(stage2[1]));
    mux2X1 s2_2 (.a(stage1[2]), .b(stage1[4]), .sel(ctrl[1]), .y(stage2[2]));
    mux2X1 s2_3 (.a(stage1[3]), .b(stage1[5]), .sel(ctrl[1]), .y(stage2[3]));
    mux2X1 s2_4 (.a(stage1[4]), .b(stage1[6]), .sel(ctrl[1]), .y(stage2[4]));
    mux2X1 s2_5 (.a(stage1[5]), .b(stage1[7]), .sel(ctrl[1]), .y(stage2[5]));
    mux2X1 s2_6 (.a(stage1[6]), .b(1'b0), .sel(ctrl[1]), .y(stage2[6]));
    mux2X1 s2_7 (.a(stage1[7]), .b(1'b0), .sel(ctrl[1]), .y(stage2[7]));

    // Stage 3: shift right by 1 when ctrl[0] is high
    mux2X1 s3_0 (.a(stage2[0]), .b(stage2[1]), .sel(ctrl[0]), .y(stage3[0]));
    mux2X1 s3_1 (.a(stage2[1]), .b(stage2[2]), .sel(ctrl[0]), .y(stage3[1]));
    mux2X1 s3_2 (.a(stage2[2]), .b(stage2[3]), .sel(ctrl[0]), .y(stage3[2]));
    mux2X1 s3_3 (.a(stage2[3]), .b(stage2[4]), .sel(ctrl[0]), .y(stage3[3]));
    mux2X1 s3_4 (.a(stage2[4]), .b(stage2[5]), .sel(ctrl[0]), .y(stage3[4]));
    mux2X1 s3_5 (.a(stage2[5]), .b(stage2[6]), .sel(ctrl[0]), .y(stage3[5]));
    mux2X1 s3_6 (.a(stage2[6]), .b(stage2[7]), .sel(ctrl[0]), .y(stage3[6]));
    mux2X1 s3_7 (.a(stage2[7]), .b(1'b0), .sel(ctrl[0]), .y(stage3[7]));

    assign out = stage3;

endmodule
