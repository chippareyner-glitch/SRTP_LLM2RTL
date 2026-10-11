module synchronizer (
    input  logic       clk_a,
    input  logic       clk_b,
    input  logic       arstn,
    input  logic       brstn,
    input  logic [3:0] data_in,
    input  logic       data_en,
    output logic [3:0] dataout
);

    logic [3:0] data_reg;
    logic       en_data_reg;
    logic       en_clap_one;
    logic       en_clap_two;

    // clk_a domain: capture data and enable
    always_ff @(posedge clk_a or negedge arstn) begin
        if (!arstn) begin
            data_reg    <= 4'b0;
            en_data_reg <= 1'b0;
        end else begin
            data_reg    <= data_in;
            en_data_reg <= data_en;
        end
    end

    // clk_b domain: synchronize the enable with two flops
    always_ff @(posedge clk_b or negedge brstn) begin
        if (!brstn) begin
            en_clap_one <= 1'b0;
            en_clap_two <= 1'b0;
        end else begin
            en_clap_one <= en_data_reg;
            en_clap_two <= en_clap_one;
        end
    end

    // Output MUX/latch controlled by the second synchronized enable
    always_latch begin
        if (!brstn) begin
            dataout = 4'b0;
        end else if (en_clap_two) begin
            dataout = data_reg;
        end
    end

endmodule
