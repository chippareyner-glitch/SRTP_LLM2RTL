module TopModule(
    input  clk,
    input  d,
    output logic q
);

    always_ff @(posedge clk) begin
        q <= d;
    end

endmodule
