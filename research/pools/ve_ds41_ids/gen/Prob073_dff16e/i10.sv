module TopModule (
    input  wire        clk,
    input  wire        resetn,
    input  wire [1:0]  byteena,
    input  wire [15:0] d,
    output logic [15:0] q
);

    always_ff @(posedge clk) begin
        if (!resetn) begin
            q <= 16'b0;
        end else begin
            if (byteena[0])
                q[7:0] <= d[7:0];
            if (byteena[1])
                q[15:8] <= d[15:8];
        end
    end

endmodule
