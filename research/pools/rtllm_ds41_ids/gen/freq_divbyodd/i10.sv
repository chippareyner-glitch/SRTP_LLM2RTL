module freq_divbyodd #(
    parameter NUM_DIV = 5
) (
    input  wire clk,
    input  wire rst_n,
    output wire clk_div
);

    localparam integer WIDTH = (NUM_DIV > 1) ? $clog2(NUM_DIV) : 1;
    localparam integer HALF  = NUM_DIV / 2;

    reg [WIDTH-1:0] cnt1;
    reg [WIDTH-1:0] cnt2;
    reg clk_div1;
    reg clk_div2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt1     <= {WIDTH{1'b0}};
            clk_div1 <= 1'b1;
        end
        else if (cnt1 == NUM_DIV - 1) begin
            cnt1     <= {WIDTH{1'b0}};
            clk_div1 <= 1'b1;
        end
        else begin
            cnt1 <= cnt1 + 1'b1;
            if ((cnt1 + 1'b1) < HALF)
                clk_div1 <= 1'b1;
            else
                clk_div1 <= 1'b0;
        end
    end

    always_ff @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt2     <= {WIDTH{1'b0}};
            clk_div2 <= 1'b1;
        end
        else if (cnt2 == NUM_DIV - 1) begin
            cnt2     <= {WIDTH{1'b0}};
            clk_div2 <= 1'b1;
        end
        else begin
            cnt2 <= cnt2 + 1'b1;
            if ((cnt2 + 1'b1) < HALF)
                clk_div2 <= 1'b1;
            else
                clk_div2 <= 1'b0;
        end
    end

    assign clk_div = clk_div1 | clk_div2;

endmodule
