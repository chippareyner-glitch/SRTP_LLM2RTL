module multi_booth_8bit (
    input  wire               clk,
    input  wire               reset,
    input  wire [7:0]         a,
    input  wire [7:0]         b,
    output reg  signed [15:0] p,
    output reg                rdy
);

    reg signed [15:0] multiplier;
    reg signed [15:0] multiplicand;
    reg        [4:0]  ctr;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            multiplier   <= {{8{a[7]}}, a};
            multiplicand <= {{8{b[7]}}, b};
            p            <= 16'sd0;
            ctr          <= 5'd0;
            rdy          <= 1'b0;
        end else begin
            if (ctr < 5'd16) begin
                multiplicand <= multiplicand << 1;
                if (multiplier[ctr])
                    p <= p + multiplicand;
                ctr <= ctr + 1'b1;
            end else begin
                rdy <= 1'b1;
            end
        end
    end

endmodule
