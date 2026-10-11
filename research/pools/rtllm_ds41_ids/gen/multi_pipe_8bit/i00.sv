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

    logic [15:0] temp [0:7];
    logic [15:0] sum  [0:3];
    logic [15:0] mul_out_reg;

    always_comb begin
        for (int i = 0; i < 8; i++) begin
            temp[i] = mul_b_reg[i] ? ({{8{1'b0}}, mul_a_reg} << i) : 16'd0;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mul_a_reg      <= 8'd0;
            mul_b_reg      <= 8'd0;
            mul_en_out_reg <= 3'd0;
            for (int i = 0; i < 4; i++) begin
                sum[i] <= 16'd0;
            end
            mul_out_reg    <= 16'd0;
        end else begin
            // Stage 1: input registers and input enable
            if (mul_en_in) begin
                mul_a_reg <= mul_a;
                mul_b_reg <= mul_b;
            end
            mul_en_out_reg[0] <= mul_en_in;

            // Stage 2: partial sums
            if (mul_en_out_reg[0]) begin
                sum[0] <= temp[0] + temp[1];
                sum[1] <= temp[2] + temp[3];
                sum[2] <= temp[4] + temp[5];
                sum[3] <= temp[6] + temp[7];
            end
            mul_en_out_reg[1] <= mul_en_out_reg[0];

            // Stage 3: final product
            if (mul_en_out_reg[1]) begin
                mul_out_reg <= sum[0] + sum[1] + sum[2] + sum[3];
            end
            mul_en_out_reg[2] <= mul_en_out_reg[1];
        end
    end

    assign mul_en_out = mul_en_out_reg[2];
    assign mul_out    = mul_en_out ? mul_out_reg : 16'd0;

endmodule
