module TopModule (
    input  logic        clk,
    input  logic        reset,
    output logic [31:0] q
);

    logic [31:0] next_q;

    always_comb begin
        next_q = {1'b0, q[31:1]};
        if (q[0])
            next_q = next_q ^ 32'h80200003;
    end

    always_ff @(posedge clk) begin
        if (reset)
            q <= 32'h1;
        else
            q <= next_q;
    end

endmodule
