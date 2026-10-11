module freq_divbyodd #(
    parameter NUM_DIV = 5
) (
    input  logic clk,
    input  logic rst_n,
    output logic clk_div
);

    localparam HALF = NUM_DIV / 2;
    localparam CNT_WIDTH = (NUM_DIV <= 1) ? 1 : $clog2(NUM_DIV);

    logic [CNT_WIDTH-1:0] cnt1, cnt2;
    logic clk_div1, clk_div2;
    logic [CNT_WIDTH-1:0] cnt1_next, cnt2_next;

    assign cnt1_next = (cnt1 == NUM_DIV - 1) ? '0 : cnt1 + 1'b1;
    assign cnt2_next = (cnt2 == NUM_DIV - 1) ? '0 : cnt2 + 1'b1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= '0;
            clk_div1 <= 1'b1;
        end else begin
            cnt1     <= cnt1_next;
            clk_div1 <= (cnt1_next < HALF) ? 1'b1 : 1'b0;
        end
    end

    always_ff @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= '0;
            clk_div2 <= 1'b1;
        end else begin
            cnt2     <= cnt2_next;
            clk_div2 <= (cnt2_next < HALF) ? 1'b1 : 1'b0;
        end
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
