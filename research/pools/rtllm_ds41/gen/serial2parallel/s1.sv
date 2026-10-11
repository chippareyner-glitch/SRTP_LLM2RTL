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
            shift_reg     <= 8'b0;
            cnt           <= 4'd0;
            dout_parallel <= 8'b0;
            dout_valid    <= 1'b0;
        end else begin
            dout_valid <= 1'b0;

            if (!dout_valid && din_valid) begin
                if (cnt == 4'd7) begin
                    dout_parallel <= {shift_reg[6:0], din_serial};
                    dout_valid    <= 1'b1;
                    cnt           <= 4'd0;
                end else begin
                    shift_reg <= {shift_reg[6:0], din_serial};
                    cnt       <= cnt + 4'd1;
                end
            end
        end
    end

endmodule
