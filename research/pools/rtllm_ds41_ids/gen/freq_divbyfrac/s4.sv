module freq_divbyfrac (
    input  wire clk,
    input  wire rst_n,
    output wire clk_div
);

    parameter MUL2_DIV_CLK = 7;

    reg [2:0] cnt;
    reg       clk_div1;
    reg       clk_div2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 3'd0;
        else if (cnt == MUL2_DIV_CLK - 1)
            cnt <= 3'd0;
        else
            cnt <= cnt + 3'd1;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div1 <= 1'b0;
        else if (cnt == 3'd0 || cnt == 3'd4)
            clk_div1 <= 1'b1;
        else
            clk_div1 <= 1'b0;
    end

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div2 <= 1'b0;
        else if (cnt == 3'd1 || cnt == 3'd4)
            clk_div2 <= 1'b1;
        else
            clk_div2 <= 1'b0;
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
