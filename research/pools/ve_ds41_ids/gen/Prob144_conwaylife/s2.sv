module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] next_q;
    integer       i, r, c, dr, dc, nr, nc;
    logic [3:0]   cnt;

    always_comb begin
        next_q = 256'b0;

        for (i = 0; i < 256; i = i + 1) begin
            r = i / 16;
            c = i % 16;
            cnt = 4'd0;

            for (dr = -1; dr <= 1; dr = dr + 1) begin
                for (dc = -1; dc <= 1; dc = dc + 1) begin
                    if (!(dr == 0 && dc == 0)) begin
                        nr = (r + dr + 16) % 16;
                        nc = (c + dc + 16) % 16;
                        cnt = cnt + q[nr * 16 + nc];
                    end
                end
            end

            next_q[i] = (cnt == 4'd3) || (q[i] && cnt == 4'd2);
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
