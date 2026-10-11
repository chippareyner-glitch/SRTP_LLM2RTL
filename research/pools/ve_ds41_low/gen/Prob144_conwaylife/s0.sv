module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output reg  [255:0] q
);

    wire [255:0] next_q;

    genvar r, c;
    generate
        for (r = 0; r < 16; r = r + 1) begin : row_gen
            for (c = 0; c < 16; c = c + 1) begin : col_gen
                wire [3:0] up = (r == 0)  ? 4'd15 : r - 1;
                wire [3:0] dn = (r == 15) ? 4'd0  : r + 1;
                wire [3:0] lf = (c == 0)  ? 4'd15 : c - 1;
                wire [3:0] rt = (c == 15) ? 4'd0  : c + 1;

                wire [4:0] nbrs =
                      q[up*16 + lf] + q[up*16 + c]  + q[up*16 + rt]
                    + q[r*16  + lf]                 + q[r*16  + rt]
                    + q[dn*16 + lf] + q[dn*16 + c]  + q[dn*16 + rt];

                assign next_q[r*16 + c] = (nbrs == 5'd2) ? q[r*16 + c]
                                        : (nbrs == 5'd3);
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
