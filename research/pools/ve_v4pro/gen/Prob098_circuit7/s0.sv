module TopModule (
    input  logic clk,
    input  logic a,
    output logic q
);

    logic d;

    always_ff @(posedge clk) begin
        d <= ~a;
        q <= d;
    end

endmodule
