module freq_divbyodd #(
    parameter NUM_DIV = 5
) (
    input  wire clk,
    input  wire rst_n,
    output wire clk_div
);

    localparam integer WIDTH = (NUM_DIV < 2) ? 1 : $clog2(NUM_DIV);
    localparam integer HALF  = NUM_DIV / 2;  // integer truncation for odd NUM_DIV

    reg [WIDTH-1:0] cnt1;
    reg [WIDTH-1:0] cnt2;
    reg             clk_div1;
    reg             clk_div2;

    wire [WIDTH-1:0] cnt1_next = (cnt1 == NUM_DIV-1) ? {WIDTH{1'b0}} : cnt1 + 1'b1;
    wire [WIDTH-1:0] cnt2_next = (cnt2 == NUM_DIV-1) ? {WIDTH{1'b0}} : cnt2 + 1'b1;

    // Positive-edge counter / divider
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= {WIDTH{1'b0}};
            clk_div1 <= 1'b1;
        end else begin
            cnt1     <= cnt1_next;
            clk_div1 <= (cnt1_next < HALF) ? 1'b1 : 1'b0;
        end
    end

    // Negative-edge counter / divider
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= {WIDTH{1'b0}};
            clk_div2 <= 1'b1;
        end else begin
            cnt2     <= cnt2_next;
            clk_div2 <= (cnt2_next < HALF) ? 1'b1 : 1'b0;
        end
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
