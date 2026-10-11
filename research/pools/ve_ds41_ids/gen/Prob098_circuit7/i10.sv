module TopModule (
    input  clk,
    input  a,
    output logic q
);

    logic a_d;

    always_ff @(posedge clk) begin
        a_d <= a;
        q   <= ~a_d;
    end

endmodule
