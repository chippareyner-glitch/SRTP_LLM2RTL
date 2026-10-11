module LFSR (
    input  logic       clk,
    input  logic       rst,
    output logic [3:0] out
);

    always_ff @(posedge clk) begin
        if (rst) begin
            out <= 4'b0000;
        end else begin
            out <= {out[2:0], ~(out[3] ^ out[2])};
        end
    end

endmodule
