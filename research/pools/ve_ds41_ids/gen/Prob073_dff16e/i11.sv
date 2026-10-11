module TopModule (
    input  logic        clk,
    input  logic        resetn,
    input  logic [1:0]  byteena,
    input  logic [15:0] d,
    output logic [15:0] q
);

    always_ff @(posedge clk) begin
        if (byteena[1])
            q[15:8] <= d[15:8];
        else if (!resetn)
            q[15:8] <= 8'b0;

        if (byteena[0])
            q[7:0] <= d[7:0];
        else if (!resetn)
            q[7:0] <= 8'b0;
    end

endmodule
