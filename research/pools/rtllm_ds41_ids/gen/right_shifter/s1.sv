module right_shifter (
    input  logic       clk,
    input  logic       d,
    output logic [7:0] q
);

    initial q = 8'b0;

    always_ff @(posedge clk) begin
        q <= {d, q[7:1]};
    end

endmodule
