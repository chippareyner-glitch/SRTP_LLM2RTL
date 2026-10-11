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

    logic [7:0] stage4;
    logic [7:0] stage2;

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_shift_by_4
            mux2X1 u_mux (
                .a   (in[i]),
                .b   ((i + 4 < 8) ? in[i + 4] : 1'b0),
                .sel (ctrl[2]),
                .y   (stage4[i])
            );
        end
    endgenerate

    genvar j;
    generate
        for (j = 0; j < 8; j = j + 1) begin : gen_shift_by_2
            mux2X1 u_mux (
                .a   (stage4[j]),
                .b   ((j + 2 < 8) ? stage4[j + 2] : 1'b0),
                .sel (ctrl[1]),
                .y   (stage2[j])
            );
        end
    endgenerate

    genvar k;
    generate
        for (k = 0; k < 8; k = k + 1) begin : gen_shift_by_1
            mux2X1 u_mux (
                .a   (stage2[k]),
                .b   ((k + 1 < 8) ? stage2[k + 1] : 1'b0),
                .sel (ctrl[0]),
                .y   (out[k])
            );
        end
    endgenerate

endmodule
