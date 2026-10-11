module div_16bit(
    input  [15:0] A,
    input  [7:0]  B,
    output reg [15:0] result,
    output reg [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0]  b_reg;

    always @(*) begin
        a_reg = A;
        b_reg = B;
    end

    always @(*) begin
        integer i;
        reg [15:0] remainder;
        remainder = 16'b0;
        for (i = 15; i >= 0; i = i - 1) begin
            remainder = {remainder[14:0], a_reg[i]};
            if (remainder >= {8'b0, b_reg}) begin
                remainder = remainder - {8'b0, b_reg};
                result[i] = 1'b1;
            end else begin
                result[i] = 1'b0;
            end
        end
        odd = remainder;
    end

endmodule
