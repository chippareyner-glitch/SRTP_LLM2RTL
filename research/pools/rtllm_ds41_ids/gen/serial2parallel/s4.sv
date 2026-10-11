module serial2parallel (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       din_serial,
    input  logic       din_valid,
    output logic [7:0] dout_parallel,
    output logic       dout_valid
);

    logic [7:0] shift_reg;
    logic [3:0] cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt           <= 4'd0;
            shift_reg     <= 8'd0;
            dout_parallel <= 8'd0;
            dout_valid    <= 1'b0;
        end else begin
            dout_valid <= 1'b0;

            if (cnt == 4'd8) begin
                cnt <= 4'd0;
            end else if (cnt == 4'd7 && din_valid) begin
                shift_reg     <= {shift_reg[6:0], din_serial};
                dout_parallel <= {shift_reg[6:0], din_serial};
                cnt           <= 4'd8;
                dout_valid    <= 1'b1;
            end else if (din_valid) begin
                shift_reg <= {shift_reg[6:0], din_serial};
                cnt       <= cnt + 4'd1;
            end
        end
    end

endmodule
