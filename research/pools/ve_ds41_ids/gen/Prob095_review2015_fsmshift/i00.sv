module TopModule(
    input  logic clk,
    input  logic reset,
    output logic shift_ena
);

    logic [3:0] shift_reg;

    always_ff @(posedge clk) begin
        if (reset)
            shift_reg <= 4'b1111;
        else
            shift_reg <= {shift_reg[2:0], 1'b0};
    end

    assign shift_ena = shift_reg[3];

endmodule
