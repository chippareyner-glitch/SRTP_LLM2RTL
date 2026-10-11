module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic ena,
    output logic pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    always_ff @(posedge clk) begin
        if (reset) begin
            pm <= 1'b0;
            hh <= 8'h12;
            mm <= 8'h00;
            ss <= 8'h00;
        end else if (ena) begin
            if (ss == 8'h59) begin
                ss <= 8'h00;
                if (mm == 8'h59) begin
                    mm <= 8'h00;
                    if (hh == 8'h12) begin
                        hh <= 8'h01;
                    end else if (hh == 8'h11) begin
                        hh <= 8'h12;
                        pm <= ~pm;
                    end else begin
                        if (hh[3:0] == 4'h9) begin
                            hh <= {hh[7:4] + 1'b1, 4'h0};
                        end else begin
                            hh <= {hh[7:4], hh[3:0] + 1'b1};
                        end
                    end
                end else begin
                    if (mm[3:0] == 4'h9) begin
                        mm <= {mm[7:4] + 1'b1, 4'h0};
                    end else begin
                        mm <= {mm[7:4], mm[3:0] + 1'b1};
                    end
                end
            end else begin
                if (ss[3:0] == 4'h9) begin
                    ss <= {ss[7:4] + 1'b1, 4'h0};
                end else begin
                    ss <= {ss[7:4], ss[3:0] + 1'b1};
                end
            end
        end
    end

endmodule
