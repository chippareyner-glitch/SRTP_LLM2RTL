module multi_pipe_8bit (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        mul_en_in,
    input  logic [7:0]  mul_a,
    input  logic [7:0]  mul_b,
    output logic        mul_en_out,
    output logic [15:0] mul_out
);

    logic [7:0]  mul_a_reg;
    logic [7:0]  mul_b_reg;
    logic [3:0]  mul_en_out_reg;
    logic [15:0] temp [0:7];
    logic [15:0] sum1 [0:3];
    logic [15:0] sum2 [0:1];
    logic [15:0] mul_out_reg;

    // Input registers, updated only when input enable is active
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_a_reg <= 8'd0;
            mul_b_reg <= 8'd0;
        end else if (mul_en_in) begin
            mul_a_reg <= mul_a;
            mul_b_reg <= mul_b;
        end
    end

    // Enable pipeline (4 cycles deep)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_en_out_reg <= 4'd0;
        end else begin
            mul_en_out_reg <= {mul_en_out_reg[2:0], mul_en_in};
        end
    end

    // Partial product generation
    assign temp[0] = mul_b_reg[0] ? {8'b0, mul_a_reg}        : 16'b0;
    assign temp[1] = mul_b_reg[1] ? {7'b0, mul_a_reg, 1'b0}  : 16'b0;
    assign temp[2] = mul_b_reg[2] ? {6'b0, mul_a_reg, 2'b0}  : 16'b0;
    assign temp[3] = mul_b_reg[3] ? {5'b0, mul_a_reg, 3'b0}  : 16'b0;
    assign temp[4] = mul_b_reg[4] ? {4'b0, mul_a_reg, 4'b0}  : 16'b0;
    assign temp[5] = mul_b_reg[5] ? {3'b0, mul_a_reg, 5'b0}  : 16'b0;
    assign temp[6] = mul_b_reg[6] ? {2'b0, mul_a_reg, 6'b0}  : 16'b0;
    assign temp[7] = mul_b_reg[7] ? {1'b0, mul_a_reg, 7'b0}  : 16'b0;

    // Partial sum stage 1: pairwise addition
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum1[0] <= 16'd0;
            sum1[1] <= 16'd0;
            sum1[2] <= 16'd0;
            sum1[3] <= 16'd0;
        end else begin
            sum1[0] <= temp[0] + temp[1];
            sum1[1] <= temp[2] + temp[3];
            sum1[2] <= temp[4] + temp[5];
            sum1[3] <= temp[6] + temp[7];
        end
    end

    // Partial sum stage 2: combine pairwise sums
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum2[0] <= 16'd0;
            sum2[1] <= 16'd0;
        end else begin
            sum2[0] <= sum1[0] + sum1[1];
            sum2[1] <= sum1[2] + sum1[3];
        end
    end

    // Final product accumulation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_out_reg <= 16'd0;
        end else begin
            mul_out_reg <= sum2[0] + sum2[1];
        end
    end

    // Output assignments
    assign mul_en_out = mul_en_out_reg[3];
    assign mul_out    = mul_en_out ? mul_out_reg : 16'd0;

endmodule
