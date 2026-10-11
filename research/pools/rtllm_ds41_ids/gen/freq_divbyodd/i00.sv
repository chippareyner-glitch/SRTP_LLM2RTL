module freq_divbyodd #(
    parameter integer NUM_DIV = 5
) (
    input  wire clk,
    input  wire rst_n,
    output wire clk_div
);

    localparam integer HALF_DIV  = NUM_DIV / 2;
    localparam integer CNT_WIDTH = (NUM_DIV > 1) ? $clog2(NUM_DIV) : 1;

    logic [CNT_WIDTH-1:0] cnt1;
    logic [CNT_WIDTH-1:0] cnt2;
    logic clk_div1;
    logic clk_div2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= {CNT_WIDTH{1'b0}};
            clk_div1 <= 1'b1;
        end else begin
            if (cnt1 == NUM_DIV - 1) begin
                cnt1     <= {CNT_WIDTH{1'b0}};
                clk_div1 <= 1'b1;
            end else begin
                cnt1 <= cnt1 + 1'b1;
                if ((cnt1 + 1'b1) < HALF_DIV)
                    clk_div1 <= 1'b1;
                else
                    clk_div1 <= 1'b0;
            end
        end
    end

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= {CNT_WIDTH{1'b0}};
            clk_div2 <= 1'b1;
        end else begin
            if (cnt2 == NUM_DIV - 1) begin
                cnt2     <= {CNT_WIDTH{1'b0}};
                clk_div2 <= 1'b1;
            end else begin
                cnt2 <= cnt2 + 1'b1;
                if ((cnt2 + 1'b1) < HALF_DIV)
                    clk_div2 <= 1'b1;
                else
                    clk_div2 <= 1'b0;
            end
        end
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
