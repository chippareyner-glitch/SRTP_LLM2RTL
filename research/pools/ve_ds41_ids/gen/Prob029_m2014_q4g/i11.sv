module TopModule (
    input  logic clk,
    input  logic rst,
    input  logic in1,
    input  logic in2,
    input  logic in3,
    output logic out
);

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            out <= 1'b0;
        end else begin
            out <= ~(in1 ^ in2) ^ in3;
        end
    end

endmodule
