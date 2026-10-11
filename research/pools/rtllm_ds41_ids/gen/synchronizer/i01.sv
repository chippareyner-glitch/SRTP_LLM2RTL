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

    always_ff @(posedge clk_a or negedge arstn) begin
        if (!arstn)
            data_reg <= 4'b0000;
        else
            data_reg <= data_in;
    end

    always_ff @(posedge clk_a or negedge arstn) begin
        if (!arstn)
            en_data_reg <= 1'b0;
        else
            en_data_reg <= data_en;
    end

    always_ff @(posedge clk_b or negedge brstn) begin
        if (!brstn) begin
            en_clap_one <= 1'b0;
            en_clap_two <= 1'b0;
        end else begin
            en_clap_one <= data_en;
            en_clap_two <= en_clap_one;
        end
    end

    always_ff @(posedge clk_b or negedge brstn) begin
        if (!brstn)
            dataout <= 4'b0000;
        else if (en_clap_two)
            dataout <= data_reg;
    end

endmodule
