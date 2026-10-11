module freq_divbyfrac (
    input  logic clk,
    input  logic rst_n,
    output logic clk_div
);

    parameter int MUL2_DIV_CLK = 7;

    logic [2:0] cnt;
    logic       clk_div_pos;
    logic       clk_div_neg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 3'b000;
        else if (cnt == MUL2_DIV_CLK - 1)
            cnt <= 3'b000;
        else
            cnt <= cnt + 1'b1;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div_pos <= 1'b0;
        else if (cnt == 3'd0 || cnt == 3'd4)
            clk_div_pos <= 1'b1;
        else
            clk_div_pos <= 1'b0;
    end

    always_ff @(negedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div_neg <= 1'b0;
        else if (cnt == 3'd1 || cnt == 3'd4)
            clk_div_neg <= 1'b1;
        else
            clk_div_neg <= 1'b0;
    end

    assign clk_div = clk_div_pos | clk_div_neg;

endmodule
