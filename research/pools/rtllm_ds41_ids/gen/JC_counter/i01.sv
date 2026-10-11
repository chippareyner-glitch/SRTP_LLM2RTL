module JC_counter (
    input  logic        clk,
    input  logic        rst_n,
    output logic [63:0] Q
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            Q <= 64'b0;
        end else if (!Q[0]) begin
            Q <= {1'b1, Q[63:1]};
        end else begin
            Q <= {1'b0, Q[63:1]};
        end
    end

endmodule
