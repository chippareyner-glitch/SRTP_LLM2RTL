module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic in,
    output logic out
);

    logic q1, q2, q3, q4;

    always_ff @(posedge clk) begin
        if (!resetn) begin
            q1 <= 1'b0;
            q2 <= 1'b0;
            q3 <= 1'b0;
            q4 <= 1'b0;
        end else begin
            q1 <= in;
            q2 <= q1;
            q3 <= q2;
            q4 <= q3;
        end
    end

    assign out = q4;

endmodule
