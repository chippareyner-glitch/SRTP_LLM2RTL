module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    output logic start_shifting
);
    logic [3:0] shift_reg;

    always_ff @(posedge clk) begin
        if (reset) begin
            shift_reg <= '0;
        end else begin
            shift_reg <= {shift_reg[2:0], data};
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            start_shifting <= 1'b0;
        end else if (shift_reg[2:0] == 3'b110 && data == 1'b1) begin
            start_shifting <= 1'b1;
        end
    end
endmodule
