module TopModule (
    input  logic clk,
    input  logic load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] next;

    integer i, r, c, dr, dc, nr, nc, sum;

    always_comb begin
        for (i = 0; i < 256; i = i + 1) begin
            r = i >> 4;
            c = i & 15;
            sum = 0;

            for (dr = -1; dr <= 1; dr = dr + 1) begin
                for (dc = -1; dc <= 1; dc = dc + 1) begin
                    if (!((dr == 0) && (dc == 0))) begin
                        nr = (r + dr + 16) & 15;
                        nc = (c + dc + 16) & 15;
                        sum = sum + q[(nr << 4) | nc];
                    end
                end
            end

            next[i] = (sum == 3) || ((sum == 2) && q[i]);
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next;
    end

endmodule
