module TopModule(
    input  logic clk,
    input  logic reset,
    output logic [31:0] q
);

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 32'h1;
        end else begin
            q <= {q[0], q[31:23], q[22]^q[0], q[21:3], q[2]^q[0], q[1]^q[0]};
        end
    end

endmodule
