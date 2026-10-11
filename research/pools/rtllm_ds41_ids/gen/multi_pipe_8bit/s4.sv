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
    logic [2:0]  mul_en_out_reg;

    wire  [15:0] temp [0:7];
    logic [15:0] sum  [0:3];
    logic [15:0] mul_out_reg;

    assign mul_en_out = mul_en_out_reg[2];
    assign mul_out    = mul_en_out ? mul_out_reg : 16'd0;

    // Input registers and enable pipeline
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_a_reg      <= 8'd0;
            mul_b_reg      <= 8'd0;
            mul_en_out_reg <= 3'd0;
        end else begin
            mul_en_out_reg <= {mul_en_out_reg[1:0], mul_en_in};

            if (mul_en_in) begin
                mul_a_reg <= mul_a;
                mul_b_reg <= mul_b;
            end
        end
    end

    // Partial product generation
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_partial_products
            assign temp[i] = mul_b_reg[i] ? ({8'b0, mul_a_reg} << i) : 16'd0;
        end
    endgenerate

    // Partial sum calculation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum[0] <= 16'd0;
            sum[1] <= 16'd0;
            sum[2] <= 16'd0;
            sum[3] <= 16'd0;
        end else if (mul_en_out_reg[0]) begin
            sum[0] <= temp[0] + temp[1];
            sum[1] <= temp[2] + temp[3];
            sum[2] <= temp[4] + temp[5];
            sum[3] <= temp[6] + temp[7];
        end
    end

    // Final product calculation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_out_reg <= 16'd0;
        end else if (mul_en_out_reg[1]) begin
            mul_out_reg <= sum[0] + sum[1] + sum[2] + sum[3];
        end
    end

endmodule
