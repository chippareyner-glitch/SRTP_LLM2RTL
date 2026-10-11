module div_16bit(
    input  [15:0] A,
    input  [7:0]  B,
    output reg [15:0] result,
    output reg [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0]  b_reg;
    reg [8:0]  rem;
    integer    i;

    always @(*) begin
        a_reg = A;
        b_reg = B;
    end

    always @(*) begin
        result = 16'd0;
        odd    = 16'd0;
        rem    = 9'd0;

        for (i = 15; i >= 0; i = i - 1) begin
            rem = {rem[7:0], a_reg[i]};
            if (rem >= {1'b0, b_reg}) begin
                rem = rem - {1'b0, b_reg};
                result[i] = 1'b1;
            end else begin
                result[i] = 1'b0;
            end
        end

        odd = {8'd0, rem[7:0]};
    end

endmodule
