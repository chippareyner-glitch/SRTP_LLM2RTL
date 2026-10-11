module TopModule (
    input clk,
    input a,
    output logic q
);

    logic [1:0] shift_reg;

    always_ff @(posedge clk) begin
        shift_reg <= {shift_reg[0], a};
    end

    assign q = ~shift_reg[1];

endmodule
