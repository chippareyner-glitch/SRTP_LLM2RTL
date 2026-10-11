module freq_div (
    input  logic CLK_in,
    input  logic RST,
    output logic CLK_50,
    output logic CLK_10,
    output logic CLK_1
);

    logic [2:0] cnt_10;
    logic [5:0] cnt_100;

    always_ff @(posedge CLK_in or posedge RST) begin
        if (RST) begin
            CLK_50 <= 1'b0;
        end else begin
            CLK_50 <= ~CLK_50;
        end
    end

    always_ff @(posedge CLK_in or posedge RST) begin
        if (RST) begin
            CLK_10  <= 1'b0;
            cnt_10  <= 3'd0;
        end else begin
            if (cnt_10 == 3'd4) begin
                CLK_10 <= ~CLK_10;
                cnt_10 <= 3'd0;
            end else begin
                cnt_10 <= cnt_10 + 3'd1;
            end
        end
    end

    always_ff @(posedge CLK_in or posedge RST) begin
        if (RST) begin
            CLK_1   <= 1'b0;
            cnt_100 <= 6'd0;
        end else begin
            if (cnt_100 == 6'd49) begin
                CLK_1   <= ~CLK_1;
                cnt_100 <= 6'd0;
            end else begin
                cnt_100 <= cnt_100 + 6'd1;
            end
        end
    end

endmodule
