module TopModule (
    input  logic clk,
    input  logic a,
    input  logic b,
    output logic q,
    output logic state
);

    logic next_state;

    assign q = a ^ b ^ state;
    assign next_state = (a & b) | (state & (a | b));

    always_ff @(posedge clk) begin
        state <= next_state;
    end

endmodule
