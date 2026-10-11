module TopModule (
    input  logic       clk,
    input  logic       areset,
    input  logic [7:0] d,
    output logic [7:0] q
);

    logic reset_sync;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            reset_sync <= 1'b1;
        else
            reset_sync <= 1'b0;
    end

    always_ff @(posedge clk or posedge reset_sync) begin
        if (reset_sync)
            q <= 8'b0;
        else
            q <= d;
    end

endmodule
