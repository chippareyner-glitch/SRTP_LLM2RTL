module TopModule (
    input  clk,
    input  L,
    input  q_in,
    input  r_in,
    output logic Q
);
    always_ff @(posedge clk) begin
        if (L) begin
            Q <= r_in;
        end else begin
            Q <= q_in;
        end
    end
endmodule
