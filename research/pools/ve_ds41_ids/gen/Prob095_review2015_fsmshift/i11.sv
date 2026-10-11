module TopModule (
    input logic clk,
    input logic reset,
    output logic shift_ena
);

    logic [2:0] count;

    always_ff @(posedge clk) begin
        if (reset) begin
            count <= 3'd0;
            shift_ena <= 1'b0;
        end else begin
            if (count < 3'd4) begin
                shift_ena <= 1'b1;
                count <= count + 3'd1;
            end else begin
                shift_ena <= 1'b0;
            end
        end
    end

endmodule
