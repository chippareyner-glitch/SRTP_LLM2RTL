module TopModule (
    input  clk,
    input  a,
    output logic q
);

    always_ff @(posedge clk) begin
        q <= ~a;
    end

endmodule
