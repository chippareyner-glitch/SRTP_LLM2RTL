module TopModule (
    input  logic       clk,
    input  logic [7:0] d,
    output logic [7:0] q
);

    always_ff @(posedge clk) begin
        q[7] <= d[0];
        q[6] <= d[1];
        q[5] <= d[2];
        q[4] <= d[3];
        q[3] <= d[4];
        q[2] <= d[5];
        q[1] <= d[6];
        q[0] <= d[7];
    end

endmodule
