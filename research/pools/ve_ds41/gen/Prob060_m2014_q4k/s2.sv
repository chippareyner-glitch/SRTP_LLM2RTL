module TopModule (
    input  clk,
    input  resetn,
    input  in,
    output out
);

    logic [3:0] q;

    always_ff @(posedge clk) begin
        if (!resetn)
            q <= 4'b0000;
        else
            q <= {q[2:0], in};
    end

    assign out = q[3];

endmodule
