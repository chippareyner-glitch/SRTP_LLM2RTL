module TopModule (
    input clk,
    input reset,
    input ena,
    output logic pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    logic [3:0] sec_tens, sec_ones;
    logic [3:0] min_tens, min_ones;
    logic [3:0] hour_tens, hour_ones;
    logic pm_reg;

    assign pm = pm_reg;
    assign ss = {sec_ones, sec_tens};
    assign mm = {min_ones, min_tens};
    assign hh = {hour_ones, hour_tens};

    always_ff @(posedge clk) begin
        if (reset) begin
            sec_tens <= 4'd0;
            sec_ones <= 4'd0;
            min_tens <= 4'd0;
            min_ones <= 4'd0;
            hour_tens <= 4'd1;
            hour_ones <= 4'd2;
            pm_reg <= 1'b0;
        end else if (ena) begin
            if (sec_ones == 4'd9) begin
                sec_ones <= 4'd0;
                if (sec_tens == 4'd5) begin
                    sec_tens <= 4'd0;
                    if (min_ones == 4'd9) begin
                        min_ones <= 4'd0;
                        if (min_tens == 4'd5) begin
                            min_tens <= 4'd0;
                            if (hour_tens == 1'b0) begin
                                if (hour_ones == 4'd9) begin
                                    hour_tens <= 1'b1;
                                    hour_ones <= 4'd0;
                                end else begin
                                    hour_ones <= hour_ones + 1'b1;
                                end
                            end else begin
                                if (hour_ones == 4'd0) begin
                                    hour_ones <= 4'd1;
                                end else if (hour_ones == 4'd1) begin
                                    hour_ones <= 4'd2;
                                    pm_reg <= ~pm_reg;
                                end else if (hour_ones == 4'd2) begin
                                    hour_tens <= 1'b0;
                                    hour_ones <= 4'd1;
                                end
                            end
                        end else begin
                            min_tens <= min_tens + 1'b1;
                        end
                    end else begin
                        min_ones <= min_ones + 1'b1;
                    end
                end else begin
                    sec_tens <= sec_tens + 1'b1;
                end
            end else begin
                sec_ones <= sec_ones + 1'b1;
            end
        end
    end

endmodule
