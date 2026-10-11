module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic       ena,
    output logic       pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    logic [3:0] ss_ones, ss_tens;
    logic [3:0] mm_ones, mm_tens;
    logic [3:0] hh_ones, hh_tens;

    always_ff @(posedge clk) begin
        if (reset) begin
            ss_tens <= 4'd0;
            ss_ones <= 4'd0;
            mm_tens <= 4'd0;
            mm_ones <= 4'd0;
            hh_tens <= 4'd1;
            hh_ones <= 4'd2;
            pm      <= 1'b0;
        end
        else if (ena) begin
            if (ss_ones == 4'd9) begin
                ss_ones <= 4'd0;
                if (ss_tens == 4'd5) begin
                    ss_tens <= 4'd0;
                    // carry into minutes
                    if (mm_ones == 4'd9) begin
                        mm_ones <= 4'd0;
                        if (mm_tens == 4'd5) begin
                            mm_tens <= 4'd0;
                            // carry into hours
                            if (hh_tens == 4'd1 && hh_ones == 4'd2) begin
                                hh_tens <= 4'd0;
                                hh_ones <= 4'd1;
                                pm      <= ~pm;
                            end
                            else if (hh_ones == 4'd9) begin
                                hh_ones <= 4'd0;
                                hh_tens <= hh_tens + 4'd1;
                            end
                            else begin
                                hh_ones <= hh_ones + 4'd1;
                            end
                        end
                        else begin
                            mm_tens <= mm_tens + 4'd1;
                        end
                    end
                    else begin
                        mm_ones <= mm_ones + 4'd1;
                    end
                end
                else begin
                    ss_tens <= ss_tens + 4'd1;
                end
            end
            else begin
                ss_ones <= ss_ones + 4'd1;
            end
        end
    end

    assign ss = {ss_tens, ss_ones};
    assign mm = {mm_tens, mm_ones};
    assign hh = {hh_tens, hh_ones};

endmodule
