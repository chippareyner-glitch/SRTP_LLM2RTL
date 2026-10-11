module TopModule (
    input  logic clk,
    input  logic a,
    input  logic b,
    output logic q,
    output logic state
);

    logic next_state;

    always_comb begin
        q = a ^ b ^ state;
        next_state = (a & b) | (a & state) | (b & state);
    end

    always_ff @(posedge clk) begin
        state <= next_state;
    end

endmodule
