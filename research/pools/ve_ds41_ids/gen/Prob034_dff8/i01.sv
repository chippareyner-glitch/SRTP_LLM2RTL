module TopModule (
    input  logic       clk,
    input  logic [7:0] d,
    output logic [7:0] q
);

    // 8 positive-edge-triggered D flip-flops with implicit power-on reset to 8'h00
    logic [7:0] q_reg = 8'h00;

    always_ff @(posedge clk) begin
        q_reg <= d;
    end

    assign q = q_reg;

endmodule
