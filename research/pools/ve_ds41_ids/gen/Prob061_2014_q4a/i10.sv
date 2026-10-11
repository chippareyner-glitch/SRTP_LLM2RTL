module TopModule (
    input  clk,
    input  w,
    input  R,
    input  E,
    input  L,
    output logic Q
);

    always_ff @(posedge clk) begin
        if (L)
            Q <= R;
        else if (E)
            Q <= w;
    end

endmodule
