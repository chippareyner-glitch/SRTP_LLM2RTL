module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    logic seen_one;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            seen_one <= 1'b0;
        else
            seen_one <= seen_one | x;
    end

    assign z = seen_one ? ~x : x;

endmodule
