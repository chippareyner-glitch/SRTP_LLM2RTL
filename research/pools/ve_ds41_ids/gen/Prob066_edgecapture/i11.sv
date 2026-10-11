module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] in,
    output logic [31:0] out
);

    logic [31:0] prev;

    // Previous-input register: reset does not affect this register.
    always_ff @(posedge clk) begin
        prev <= in;
    end

    // Falling-edge capture with synchronous active-high reset on out only.
    always_ff @(posedge clk) begin
        if (reset)
            out <= 32'b0;
        else
            out <= out | (~in & prev);
    end

endmodule
