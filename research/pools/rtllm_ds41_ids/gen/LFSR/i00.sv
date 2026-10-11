module LFSR (
    input  logic clk,
    input  logic rst,
    output logic [3:0] out
);

    wire feedback = ~(out[3] ^ out[2]);

    always_ff @(posedge clk) begin
        if (rst)
            out <= 4'b0000;
        else
            out <= {out[2:0], feedback};
    end

endmodule
