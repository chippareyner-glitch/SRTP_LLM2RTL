module TopModule (
    input  logic clk,
    input  logic d,
    output logic q
);

    initial q = 1'b0;

    always_ff @(posedge clk) begin
        q <= d;
    end

endmodule
