module TopModule (
    input  clk,
    input  areset,
    input  x,
    output logic z
);

    logic seen;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            seen <= 1'b0;
            z    <= 1'b0;
        end else begin
            seen <= seen | x;
            z    <= seen ? ~x : x;
        end
    end

endmodule
