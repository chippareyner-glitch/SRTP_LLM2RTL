module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic ena,
    output logic pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    logic [5:0] sec_cnt;
    logic [5:0] min_cnt;
    logic [3:0] hour_cnt;
    logic       pm_reg;

    function automatic [7:0] bin2bcd(input logic [5:0] val);
        logic [3:0] tens;
        logic [3:0] ones;
        begin
            tens = val / 10;
            ones = val % 10;
            bin2bcd = {tens, ones};
        end
    endfunction

    always_ff @(posedge clk) begin
        if (reset) begin
            sec_cnt  <= 6'd0;
            min_cnt  <= 6'd0;
            hour_cnt <= 4'd12;
            pm_reg   <= 1'b0;
        end
        else if (ena) begin
            if (sec_cnt == 6'd59) begin
                sec_cnt <= 6'd0;
                if (min_cnt == 6'd59) begin
                    min_cnt <= 6'd0;
                    if (hour_cnt == 4'd12) begin
                        hour_cnt <= 4'd1;
                    end
                    else if (hour_cnt == 4'd11) begin
                        hour_cnt <= 4'd12;
                        pm_reg   <= ~pm_reg;
                    end
                    else begin
                        hour_cnt <= hour_cnt + 4'd1;
                    end
                end
                else begin
                    min_cnt <= min_cnt + 6'd1;
                end
            end
            else begin
                sec_cnt <= sec_cnt + 6'd1;
            end
        end
    end

    assign ss = bin2bcd(sec_cnt);
    assign mm = bin2bcd(min_cnt);
    assign hh = bin2bcd({2'b00, hour_cnt});
    assign pm = pm_reg;

endmodule
