module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg [511:0] q_r;

    // Boundary cells q[-1] and q[512] are assumed to be zero.
    wire [511:0] left  = {1'b0, q_r[511:1]};   // left[i]  = q[i+1]
    wire [511:0] right = {q_r[510:0], 1'b0};   // right[i] = q[i-1]

    // Rule 110 next-state:
    // 111 -> 0, 110 -> 1, 101 -> 1, 100 -> 0
    // 011 -> 1, 010 -> 1, 001 -> 1, 000 -> 0
    wire [511:0] next = (~left & (q_r | right)) |
                        ( left &  q_r & ~right);

    always @(posedge clk) begin
        if (load)
            q_r <= data;
        else
            q_r <= next;
    end

    assign q = q_r;

endmodule
