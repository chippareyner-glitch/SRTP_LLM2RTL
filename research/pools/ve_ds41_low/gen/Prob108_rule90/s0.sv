module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output wire [511:0] q
);

    reg [511:0] q_r;

    always @(posedge clk) begin
        if (load)
            q_r <= data;
        else
            q_r <= {q_r[510:0], 1'b0} ^ {1'b0, q_r[511:1]};
    end

    assign q = q_r;

endmodule
