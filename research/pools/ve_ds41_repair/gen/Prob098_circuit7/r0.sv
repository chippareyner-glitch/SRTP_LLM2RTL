module TopModule (
    input  logic clk,
    input  logic a,
    output logic q
);

    logic prev_a;

    always_ff @(posedge clk) begin
        if (a == prev_a)
            q <= ~a;
        prev_a <= a;
    end

endmodule
