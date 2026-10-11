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

    wire [7:0] shift4;
    wire [7:0] stage4;
    wire [7:0] shift2;
    wire [7:0] stage2;
    wire [7:0] shift1;
    wire [7:0] stage1;

    assign shift4 = {4'b0000, in[7:4]};

    generate
        for (genvar i = 0; i < 8; i = i + 1) begin : gen_shift4
            mux2X1 u_mux4 (
                .a(in[i]),
                .b(shift4[i]),
                .sel(ctrl[2]),
                .y(stage4[i])
            );
        end
    endgenerate

    assign shift2 = {2'b00, stage4[7:2]};

    generate
        for (genvar i = 0; i < 8; i = i + 1) begin : gen_shift2
            mux2X1 u_mux2 (
                .a(stage4[i]),
                .b(shift2[i]),
                .sel(ctrl[1]),
                .y(stage2[i])
            );
        end
    endgenerate

    assign shift1 = {1'b0, stage2[7:1]};

    generate
        for (genvar i = 0; i < 8; i = i + 1) begin : gen_shift1
            mux2X1 u_mux1 (
                .a(stage2[i]),
                .b(shift1[i]),
                .sel(ctrl[0]),
                .y(stage1[i])
            );
        end
    endgenerate

    assign out = stage1;

endmodule
