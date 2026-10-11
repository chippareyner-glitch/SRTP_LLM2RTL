module TopModule (
    input  logic clk,
    input  logic reset,
    output logic shift_ena
);

    logic [2:0] cnt;

    always_ff @(posedge clk) begin
        if (reset) begin
            cnt <= 3'd0;
        end else if (cnt < 3'd4) begin
            cnt <= cnt + 3'd1;
        end
    end

    assign shift_ena = (cnt < 3'd4);

endmodule
