module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] next_state;

    always_comb begin
        integer idx;
        integer r;
        integer c;
        integer dr;
        integer dc;
        integer rr;
        integer cc;
        integer cnt;

        for (idx = 0; idx < 256; idx = idx + 1) begin
            r = idx / 16;
            c = idx % 16;
            cnt = 0;

            for (dr = -1; dr <= 1; dr = dr + 1) begin
                for (dc = -1; dc <= 1; dc = dc + 1) begin
                    if (!((dr == 0) && (dc == 0))) begin
                        rr = (r + dr + 16) % 16;
                        cc = (c + dc + 16) % 16;
                        cnt = cnt + q[rr * 16 + cc];
                    end
                end
            end

            if (cnt == 3)
                next_state[idx] = 1'b1;
            else if (cnt == 2)
                next_state[idx] = q[idx];
            else
                next_state[idx] = 1'b0;
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_state;
    end

endmodule
