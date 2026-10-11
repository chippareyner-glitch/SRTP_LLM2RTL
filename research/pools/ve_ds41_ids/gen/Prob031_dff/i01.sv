module TopModule (
    input  logic clk,
    input  logic d,
    input  logic q
);

    logic q_reg;

    always_ff @(posedge clk) begin
        q_reg <= d;
    end

endmodule
