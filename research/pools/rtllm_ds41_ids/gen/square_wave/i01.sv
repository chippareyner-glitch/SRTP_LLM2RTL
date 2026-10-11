module square_wave (
    input  logic       clk,
    input  logic [7:0] freq,
    output logic       wave_out
);

    logic [7:0] count    = 8'd0;
    logic       wave_reg = 1'b0;

    assign wave_out = wave_reg;

    always_ff @(posedge clk) begin
        if (count == (freq - 8'd1)) begin
            count    <= 8'd0;
            wave_reg <= ~wave_reg;
        end else begin
            count <= count + 8'd1;
        end
    end

endmodule
