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
            hh <= 8'h12;
            mm <= 8'h00;
            ss <= 8'h00;
            pm <= 1'b0;
        end else if (ena) begin
            if (ss == 8'h59) begin
                ss <= 8'h00;

                if (mm == 8'h59) begin
                    mm <= 8'h00;

                    if (hh == 8'h11) begin
                        hh <= 8'h12;
                        pm <= ~pm;
                    end else if (hh == 8'h12) begin
                        hh <= 8'h01;
                    end else begin
                        if (hh[3:0] == 4'h9) begin
                            hh[3:0] <= 4'h0;
                            hh[7:4] <= hh[7:4] + 1'b1;
                        end else begin
                            hh[3:0] <= hh[3:0] + 1'b1;
                        end
                    end
                end else begin
                    if (mm[3:0] == 4'h9) begin
                        mm[3:0] <= 4'h0;
                        mm[7:4] <= mm[7:4] + 1'b1;
                    end else begin
                        mm[3:0] <= mm[3:0] + 1'b1;
                    end
                end
            end else begin
                if (ss[3:0] == 4'h9) begin
                    ss[3:0] <= 4'h0;
                    ss[7:4] <= ss[7:4] + 1'b1;
                end else begin
                    ss[3:0] <= ss[3:0] + 1'b1;
                end
            end
        end
    end

endmodule
