module TopModule (
    input  logic clk,
    input  logic load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [511:0] next_q;

    always_comb begin
        for (int i = 0; i < 512; i++) begin
            logic left;
            logic center;
            logic right;

            center = q[i];
            left   = (i == 511) ? 1'b0 : q[i+1];
            right  = (i == 0)   ? 1'b0 : q[i-1];

            if (center)
                next_q[i] = ~(left & right);
            else
                next_q[i] = right;
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
