module TopModule (
    input  clk,
    input  in,
    output out
);

    reg ff;

    always @(posedge clk) begin
        ff <= in ^ ff;
    end

    assign out = ff;

endmodule
