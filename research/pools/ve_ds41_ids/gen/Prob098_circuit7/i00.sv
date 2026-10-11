module TopModule (
    input  logic clk,
    input  logic a,
    output logic q
);

    logic stage1;

    always_ff @(posedge clk) begin
        stage1 <= ~a;
        q      <= stage1;
    end

endmodule
