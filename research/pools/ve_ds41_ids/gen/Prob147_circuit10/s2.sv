module TopModule (
    input  logic clk,
    input  logic a,
    input  logic b,
    output logic q,
    output logic state
);

    assign q = a ^ b ^ state;

    always_ff @(posedge clk) begin
        state <= (a & b) | (a & state) | (b & state);
    end

endmodule
