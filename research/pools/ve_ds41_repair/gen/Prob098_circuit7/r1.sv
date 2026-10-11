module TopModule (
    input  logic clk,
    input  logic a,
    output logic q
);

    logic a_delay;

    always_ff @(posedge clk) begin
        a_delay <= a;
        q <= ~a_delay;
    end

endmodule
