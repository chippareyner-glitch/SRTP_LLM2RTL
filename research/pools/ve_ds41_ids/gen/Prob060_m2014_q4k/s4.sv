module TopModule(
    input  logic clk,
    input  logic resetn,
    input  logic in,
    output logic out
);
    logic [3:0] q;

    always_ff @(posedge clk) begin
        if (!resetn) begin
            q <= 4'b0000;
        end else begin
            q <= {q[2:0], in};
        end
    end

    assign out = q[3];
endmodule
