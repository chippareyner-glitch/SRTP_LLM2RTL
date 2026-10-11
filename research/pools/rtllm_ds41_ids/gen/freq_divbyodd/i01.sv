module freq_divbyodd #(
    parameter integer NUM_DIV = 5
)(
    input  wire clk,
    input  wire rst_n,
    output wire clk_div
);

    localparam integer WIDTH = (NUM_DIV < 2) ? 1 : $clog2(NUM_DIV);
    localparam integer HALF  = NUM_DIV / 2;

    reg [WIDTH-1:0] cnt1;
    reg [WIDTH-1:0] cnt2;
    reg clk_div1;
    reg clk_div2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= {WIDTH{1'b0}};
            clk_div1 <= 1'b1;
        end else begin
            if (cnt1 == NUM_DIV - 1) begin
                cnt1     <= {WIDTH{1'b0}};
                clk_div1 <= 1'b1;
            end else begin
                cnt1 <= cnt1 + 1'b1;
                if (cnt1 == HALF)
                    clk_div1 <= 1'b0;
            end
        end
    end

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= {WIDTH{1'b0}};
            clk_div2 <= 1'b1;
        end else begin
            if (cnt2 == NUM_DIV - 1) begin
                cnt2     <= {WIDTH{1'b0}};
                clk_div2 <= 1'b1;
            end else begin
                cnt2 <= cnt2 + 1'b1;
                if (cnt2 == HALF)
                    clk_div2 <= 1'b0;
            end
        end
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
