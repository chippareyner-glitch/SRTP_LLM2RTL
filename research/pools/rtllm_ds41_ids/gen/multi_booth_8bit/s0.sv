module multi_booth_8bit (
    input  logic        clk,
    input  logic        reset,
    input  logic [7:0]  a,
    input  logic [7:0]  b,
    output logic [15:0] p,
    output logic        rdy
);

    logic [15:0] multiplier;
    logic [15:0] multiplicand;
    logic [4:0]  ctr;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            multiplier   <= {{8{a[7]}}, a};
            multiplicand <= {{8{b[7]}}, b};
            p            <= 16'b0;
            ctr          <= 5'b0;
            rdy          <= 1'b0;
        end else begin
            if (ctr < 16) begin
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
