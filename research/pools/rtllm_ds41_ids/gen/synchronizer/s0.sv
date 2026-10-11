module synchronizer (
    input  logic        clk_a,
    input  logic        clk_b,
    input  logic        arstn,
    input  logic        brstn,
    input  logic [3:0]  data_in,
    input  logic        data_en,
    output logic [3:0]  dataout
);

    logic [3:0] data_reg;
    logic       en_data_reg;
    logic       en_clap_one;
    logic       en_clap_two;

    always_ff @(posedge clk_a or negedge arstn) begin
        if (!arstn) begin
            data_reg    <= 4'b0000;
            en_data_reg <= 1'b0;
        end else begin
            data_reg    <= data_in;
            en_data_reg <= data_en;
        end
    end

    always_ff @(posedge clk_b or negedge brstn) begin
        if (!brstn) begin
            en_clap_one <= 1'b0;
            en_clap_two <= 1'b0;
            dataout     <= 4'b0000;
        end else begin
            en_clap_one <= en_data_reg;
            en_clap_two <= en_clap_one;
            if (en_clap_two)
                dataout <= data_reg;
        end
    end

endmodule
