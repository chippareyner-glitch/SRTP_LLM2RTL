module div_16bit (
    input  wire [15:0] A,
    input  wire [7:0]  B,
    output reg  [15:0] result,
    output reg  [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0]  b_reg;
    reg [15:0] r;
    integer i;

    always @(A or B) begin
        a_reg = A;
        b_reg = B;
    end

    always @(A or B or a_reg or b_reg) begin
        r = 16'd0;
        result = 16'd0;
        for (i = 15; i >= 0; i = i - 1) begin
            r = {r[14:0], a_reg[i]};
            if (r >= {8'b0, b_reg}) begin
                r = r - {8'b0, b_reg};
                result[i] = 1'b1;
            end else begin
                result[i] = 1'b0;
            end
        end
        odd = r;
    end

endmodule
