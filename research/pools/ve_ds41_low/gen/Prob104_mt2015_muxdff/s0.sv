module TopModule (
    input  clk,
    input  L,
    input  q_in,
    input  r_in,
    output logic Q
);

    always @(posedge clk) begin
        if (L)
            Q <= r_in;
        else
            Q <= q_in;
    end

endmodule
