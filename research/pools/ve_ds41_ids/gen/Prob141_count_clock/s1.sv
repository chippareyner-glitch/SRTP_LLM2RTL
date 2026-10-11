module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic ena,
    output logic pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    logic [7:0] hh_reg, mm_reg, ss_reg;
    logic pm_reg;

    assign hh = hh_reg;
    assign mm = mm_reg;
    assign ss = ss_reg;
    assign pm = pm_reg;

    always_ff @(posedge clk) begin
        if (reset) begin
            hh_reg <= 8'h12;
            mm_reg <= 8'h00;
            ss_reg <= 8'h00;
            pm_reg <= 1'b0;
        end else if (ena) begin
            if (ss_reg == 8'h59) begin
                ss_reg <= 8'h00;
                if (mm_reg == 8'h59) begin
                    mm_reg <= 8'h00;
                    if (hh_reg == 8'h11) begin
                        hh_reg <= 8'h12;
                        pm_reg <= ~pm_reg;
                    end else if (hh_reg == 8'h12) begin
                        hh_reg <= 8'h01;
                    end else if (hh_reg[3:0] == 4'd9) begin
                        hh_reg <= {hh_reg[7:4] + 4'd1, 4'd0};
                    end else begin
                        hh_reg <= {hh_reg[7:4], hh_reg[3:0] + 4'd1};
                    end
                end else begin
                    if (mm_reg[3:0] == 4'd9) begin
                        mm_reg <= {mm_reg[7:4] + 4'd1, 4'd0};
                    end else begin
                        mm_reg <= {mm_reg[7:4], mm_reg[3:0] + 4'd1};
                    end
                end
            end else begin
                if (ss_reg[3:0] == 4'd9) begin
                    ss_reg <= {ss_reg[7:4] + 4'd1, 4'd0};
                end else begin
                    ss_reg <= {ss_reg[7:4], ss_reg[3:0] + 4'd1};
                end
            end
        end
    end

endmodule
