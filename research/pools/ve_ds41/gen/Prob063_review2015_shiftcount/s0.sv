module TopModule (
    input  clk,
    input  shift_ena,
    input  count_ena,
    input  data,
    output logic [3:0] q
);

    always_ff @(posedge clk) begin
        if (shift_ena)
            q <= {q[2:0], data};
        else if (count_ena)
            q <= q - 1'b1;
    end

endmodule
