module square_wave (
    input  logic       clk,
    input  logic [7:0] freq,
    output logic       wave_out
);

    logic [7:0] count;

    initial begin
        count    = 8'd0;
        wave_out = 1'b0;
    end

    always_ff @(posedge clk) begin
        if (count == freq) begin
            count    <= 8'd0;
            wave_out <= ~wave_out;
        end else begin
            count <= count + 8'd1;
        end
    end

endmodule
