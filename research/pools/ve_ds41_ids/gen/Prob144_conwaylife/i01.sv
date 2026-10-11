module TopModule(
    input  logic clk,
    input  logic load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] next;
    integer r, c;
    integer idx, rm1, rp1, cm1, cp1;
    logic [3:0] n;

    always_comb begin
        for (r = 0; r < 16; r = r + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                idx = r * 16 + c;
                rm1 = (r + 15) % 16;
                rp1 = (r + 1) % 16;
                cm1 = (c + 15) % 16;
                cp1 = (c + 1) % 16;

                n = 4'd0;
                n = n + q[rm1 * 16 + cm1];
                n = n + q[rm1 * 16 + c];
                n = n + q[rm1 * 16 + cp1];
                n = n + q[r * 16 + cm1];
                n = n + q[r * 16 + cp1];
                n = n + q[rp1 * 16 + cm1];
                n = n + q[rp1 * 16 + c];
                n = n + q[rp1 * 16 + cp1];

                if (n <= 1)
                    next[idx] = 1'b0;
                else if (n == 2)
                    next[idx] = q[idx];
                else if (n == 3)
                    next[idx] = 1'b1;
                else
                    next[idx] = 1'b0;
            end
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next;
    end

endmodule
