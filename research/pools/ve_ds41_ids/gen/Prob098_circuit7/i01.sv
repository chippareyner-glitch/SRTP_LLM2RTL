module TopModule (
    input  logic clk,
    input  logic a,
    output logic q
);

    logic prev_a;

    always @(posedge clk) begin
        if (a == prev_a) begin
            q <= ~a;
        end
        prev_a <= a;
    end

endmodule
