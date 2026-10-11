module multi_8bit (
    input  logic [7:0]  A,
    input  logic [7:0]  B,
    output logic [15:0] product
);

    always_comb begin
        product = 16'd0;
        for (int i = 0; i < 8; i++) begin
            if (B[i]) begin
                product = product + ({8'b0, A} << i);
            end
        end
    end

endmodule
