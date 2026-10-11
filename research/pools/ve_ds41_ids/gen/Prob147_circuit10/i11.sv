module TopModule (
    input  logic clk,
    input  logic a,
    input  logic b,
    output logic q,
    output logic state
);

    logic next_state;

    assign next_state = (a & b) | (state & (a | b));
    assign q = a ^ b ^ state;

    always_ff @(posedge clk) begin
        state <= next_state;
    end

    initial begin
        state = 1'b0;
    end

endmodule
