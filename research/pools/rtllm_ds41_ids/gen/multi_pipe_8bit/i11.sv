module multi_pipe_8bit (
    input clk,
    input rst_n,
    input mul_en_in,
    input [7:0] mul_a,
    input [7:0] mul_b,
    output mul_en_out,
    output [15:0] mul_out
);

    // Stage 1 registers
    reg [7:0] mul_a_reg;
    reg [7:0] mul_b_reg;

    // Enable shift register
    reg [2:0] mul_en_out_reg;

    // Partial products
    wire [15:0] temp [0:7];

    // Stage 2 registers (partial sums)
    reg [15:0] sum [0:3];

    // Stage 3 register (final product)
    reg [15:0] mul_out_reg;

    // Partial product generation
    assign temp[0] = mul_b_reg[0] ? {8'b0, mul_a_reg} : 16'b0;
    assign temp[1] = mul_b_reg[1] ? {7'b0, mul_a_reg, 1'b0} : 16'b0;
    assign temp[2] = mul_b_reg[2] ? {6'b0, mul_a_reg, 2'b0} : 16'b0;
    assign temp[3] = mul_b_reg[3] ? {5'b0, mul_a_reg, 3'b0} : 16'b0;
    assign temp[4] = mul_b_reg[4] ? {4'b0, mul_a_reg, 4'b0} : 16'b0;
    assign temp[5] = mul_b_reg[5] ? {3'b0, mul_a_reg, 5'b0} : 16'b0;
    assign temp[6] = mul_b_reg[6] ? {2'b0, mul_a_reg, 6'b0} : 16'b0;
    assign temp[7] = mul_b_reg[7] ? {1'b0, mul_a_reg, 7'b0} : 16'b0;

    // Stage 1: input registers and enable bit 0
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_a_reg <= 8'b0;
            mul_b_reg <= 8'b0;
            mul_en_out_reg[0] <= 1'b0;
        end else if (mul_en_in) begin
            mul_a_reg <= mul_a;
            mul_b_reg <= mul_b;
            mul_en_out_reg[0] <= mul_en_in;
        end
    end

    // Stage 2: partial sum registers and enable bit 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum[0] <= 16'b0;
            sum[1] <= 16'b0;
            sum[2] <= 16'b0;
            sum[3] <= 16'b0;
            mul_en_out_reg[1] <= 1'b0;
        end else if (mul_en_out_reg[0]) begin
            sum[0] <= temp[0] + temp[1];
            sum[1] <= temp[2] + temp[3];
            sum[2] <= temp[4] + temp[5];
            sum[3] <= temp[6] + temp[7];
            mul_en_out_reg[1] <= mul_en_out_reg[0];
        end
    end

    // Stage 3: final product register and enable bit 2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_out_reg <= 16'b0;
            mul_en_out_reg[2] <= 1'b0;
        end else if (mul_en_out_reg[1]) begin
            mul_out_reg <= sum[0] + sum[1] + sum[2] + sum[3];
            mul_en_out_reg[2] <= mul_en_out_reg[1];
        end
    end

    // Output assignments
    assign mul_en_out = mul_en_out_reg[2];
    assign mul_out = mul_en_out ? mul_out_reg : 16'b0;

endmodule
