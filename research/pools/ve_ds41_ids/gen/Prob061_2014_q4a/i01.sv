module TopModule (
    input  logic clk,
    input  logic w,
    input  logic R,
    input  logic E,
    input  logic L,
    output logic Q
);

    always_ff @(posedge clk) begin
        if (E)
            Q <= w;
        else if (L)
            Q <= R;
    end

endmodule
