module LFSR #(
    parameter logic [3:0] SEED = 4'b0000
) (
    input  logic clk,
    input  logic rst,
    output logic [3:0] out
);

    logic feedback;

    assign feedback = ~(out[3] ^ out[2]);

    initial out = SEED;

    always_ff @(posedge clk) begin
        if (rst) begin
            out <= 4'b0000;
        end else begin
            out <= {out[2:0], feedback};
        end
    end

endmodule
