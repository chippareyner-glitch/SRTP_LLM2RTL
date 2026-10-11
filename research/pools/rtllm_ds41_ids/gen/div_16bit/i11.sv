module div_16bit(
    input  wire        clk,
    input  wire [15:0] A,
    input  wire [7:0]  B,
    output reg  [15:0] result,
    output reg  [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0]  b_reg;
    integer i;
    reg [15:0] rem;
    reg [15:0] quo;

    always @(posedge clk) begin
        a_reg <= A;
        b_reg <= B;
    end

    always @(*) begin
        rem = 16'd0;
        quo = 16'd0;
        for (i = 15; i >= 0; i = i - 1) begin
            rem = {rem[14:0], a_reg[i]};
            if (rem >= {8'd0, b_reg}) begin
                rem = rem - {8'd0, b_reg};
                quo[i] = 1'b1;
            end else begin
                quo[i] = 1'b0;
            end
        end
        result = quo;
        odd = rem;
    end

endmodule
