module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [511:0] left;
    logic [511:0] right;
    logic [511:0] next;

    assign left  = {1'b0, q[511:1]};
    assign right = {q[510:0], 1'b0};

    assign next = (q & ~left) | (q ^ right);

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next;
    end

endmodule
