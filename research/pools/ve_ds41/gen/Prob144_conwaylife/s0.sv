module TopModule (
    input  logic clk,
    input  logic load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] next_q;

    always_comb begin
        int r, c;
        int up, down, left, right;
        int count;

        for (r = 0; r < 16; r = r + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                up    = (r == 0)  ? 15 : r - 1;
                down  = (r == 15) ? 0  : r + 1;
                left  = (c == 0)  ? 15 : c - 1;
                right = (c == 15) ? 0  : c + 1;

                count = q[up*16 + left] + q[up*16 + c] + q[up*16 + right] +
                        q[r*16 + left] + q[r*16 + right] +
                        q[down*16 + left] + q[down*16 + c] + q[down*16 + right];

                next_q[r*16 + c] = (count == 2) ? q[r*16 + c] :
                                   (count == 3) ? 1'b1 : 1'b0;
            end
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
