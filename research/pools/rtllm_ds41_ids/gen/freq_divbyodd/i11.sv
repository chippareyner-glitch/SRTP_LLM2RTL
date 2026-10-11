module freq_divbyodd #(
    parameter NUM_DIV = 5
)(
    input  wire clk,
    input  wire rst_n,
    output reg  clk_div
);

    localparam CNT_W = (NUM_DIV > 1) ? $clog2(NUM_DIV) : 1;
    localparam HALF  = NUM_DIV / 2;

    reg [CNT_W-1:0] cnt1;
    reg [CNT_W-1:0] cnt2;

    reg clk_div1;
    reg clk_div2;

    wire [CNT_W-1:0] next_cnt1;
    wire [CNT_W-1:0] next_cnt2;

    assign next_cnt1 = (cnt1 == NUM_DIV - 1) ? {CNT_W{1'b0}} : cnt1 + 1'b1;
    assign next_cnt2 = (cnt2 == NUM_DIV - 1) ? {CNT_W{1'b0}} : cnt2 + 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= {CNT_W{1'b0}};
            clk_div1 <= 1'b1;
        end else begin
            cnt1     <= next_cnt1;
            clk_div1 <= (next_cnt1 < HALF) ? 1'b1 : 1'b0;
        end
    end

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= {CNT_W{1'b0}};
            clk_div2 <= 1'b1;
        end else begin
            cnt2     <= next_cnt2;
            clk_div2 <= (next_cnt2 < HALF) ? 1'b1 : 1'b0;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_div <= 1'b1;
        end else begin
            clk_div <= clk_div1 | clk_div2;
        end
    end

endmodule
