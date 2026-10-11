module div_16bit(
    input  [15:0] A,
    input  [7:0]  B,
    output reg [15:0] result,
    output reg [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0]  b_reg;
    reg [15:0] odd_reg;
    reg [15:0] result_reg;
    integer i;

    always @(*) begin
        a_reg = A;
        b_reg = B;
    end

    always @(*) begin
        odd_reg    = 16'd0;
        result_reg = 16'd0;
        for (i = 15; i >= 0; i = i - 1) begin
            odd_reg = {odd_reg[14:0], a_reg[i]};
            if (odd_reg[15:8] >= b_reg) begin
                odd_reg[15:8] = odd_reg[15:8] - b_reg;
                result_reg[i] = 1'b1;
            end
            else begin
                result_reg[i] = 1'b0;
            end
        end
        odd    = odd_reg;
        result = result_reg;
    end

endmodule
