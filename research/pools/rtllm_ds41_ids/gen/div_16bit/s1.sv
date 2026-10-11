module div_16bit(
    input [15:0] A,
    input [7:0] B,
    output reg [15:0] result,
    output reg [15:0] odd
);

    reg [15:0] a_reg;
    reg [7:0] b_reg;
    reg [15:0] rem;
    reg [15:0] quot;
    integer i;

    // First combinational always block: latch inputs
    always @(*) begin
        a_reg = A;
        b_reg = B;
    end

    // Second combinational always block: perform restoring division
    always @(*) begin
        rem = 16'd0;
        quot = 16'd0;

        for (i = 15; i >= 0; i = i - 1) begin
            rem = {rem[14:0], a_reg[i]};
            if (rem >= {8'd0, b_reg}) begin
                rem = rem - {8'd0, b_reg};
                quot[i] = 1'b1;
            end else begin
                quot[i] = 1'b0;
            end
        end

        result = quot;
        odd = rem;
    end

endmodule
