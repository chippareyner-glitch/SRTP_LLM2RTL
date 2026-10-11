module TopModule (
    input  clk,
    input  areset,
    input  in,
    output logic out
);

    logic state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= 1'b1; // state B
        end else begin
            state <= in ? state : ~state;
        end
    end

    assign out = state;

endmodule
