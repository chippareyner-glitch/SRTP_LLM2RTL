module TopModule(
    input clk,
    input load,
    input [255:0] data,
    output reg [255:0] q
);

    reg [255:0] next_q;
    integer i, r, c, dr, dc, nr, nc, nidx;
    reg [3:0] count;

    always @(*) begin
        next_q = 256'b0;
        for (i = 0; i < 256; i = i + 1) begin
            r = i / 16;
            c = i % 16;
            count = 0;
            for (dr = -1; dr <= 1; dr = dr + 1) begin
                for (dc = -1; dc <= 1; dc = dc + 1) begin
                    if (!(dr == 0 && dc == 0)) begin
                        nr = (r + dr + 16) % 16;
                        nc = (c + dc + 16) % 16;
                        nidx = nr * 16 + nc;
                        count = count + q[nidx];
                    end
                end
            end
            if (count == 2)
                next_q[i] = q[i];
            else if (count == 3)
                next_q[i] = 1'b1;
            else
                next_q[i] = 1'b0;
        end
    end

    always @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
