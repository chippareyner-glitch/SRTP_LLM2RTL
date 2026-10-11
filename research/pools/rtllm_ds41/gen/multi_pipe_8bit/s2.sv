module multi_pipe_8bit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        mul_en_in,
    input  wire [7:0]  mul_a,
    input  wire [7:0]  mul_b,
    output wire        mul_en_out,
    output reg  [15:0] mul_out
);

    // ------------------------------------------------------------------
    // Internal registers
    // ------------------------------------------------------------------
    reg  [7:0]  mul_a_reg;        // registered multiplicand
    reg  [7:0]  mul_b_reg;        // registered multiplier
    reg  [2:0]  mul_en_out_reg;   // enable pipeline (MSB drives mul_en_out)
    reg  [15:0] sum [0:3];        // partial sum registers
    reg  [15:0] mul_out_reg;      // final product register

    // ------------------------------------------------------------------
    // Partial product wires
    // ------------------------------------------------------------------
    wire [15:0] temp [0:7];

    // ------------------------------------------------------------------
    // Stage 1 : input registers + enable shift register
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_a_reg      <= 8'd0;
            mul_b_reg      <= 8'd0;
            mul_en_out_reg <= 3'd0;
        end
        else begin
            if (mul_en_in) begin
                mul_a_reg <= mul_a;
                mul_b_reg <= mul_b;
            end
            mul_en_out_reg <= {mul_en_out_reg[1:0], mul_en_in};
        end
    end

    // ------------------------------------------------------------------
    // Partial product generation : shift-and-select of the multiplicand
    // according to each bit of the multiplier
    // ------------------------------------------------------------------
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_partial_product
            assign temp[i] = mul_b_reg[i] ? ({8'b0, mul_a_reg} << i) : 16'd0;
        end
    endgenerate

    // ------------------------------------------------------------------
    // Stage 2 : partial sum calculation (pairs of partial products)
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum[0] <= 16'd0;
            sum[1] <= 16'd0;
            sum[2] <= 16'd0;
            sum[3] <= 16'd0;
        end
        else begin
            sum[0] <= temp[0] + temp[1];
            sum[1] <= temp[2] + temp[3];
            sum[2] <= temp[4] + temp[5];
            sum[3] <= temp[6] + temp[7];
        end
    end

    // ------------------------------------------------------------------
    // Stage 3 : final product accumulation
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mul_out_reg <= 16'd0;
        else
            mul_out_reg <= sum[0] + sum[1] + sum[2] + sum[3];
    end

    // ------------------------------------------------------------------
    // Output enable derived from the MSB of the enable pipeline
    // ------------------------------------------------------------------
    assign mul_en_out = mul_en_out_reg[2];

    // ------------------------------------------------------------------
    // Output assignment : valid product or zero
    // ------------------------------------------------------------------
    always @(*) begin
        if (mul_en_out)
            mul_out = mul_out_reg;
        else
            mul_out = 16'd0;
    end

endmodule
