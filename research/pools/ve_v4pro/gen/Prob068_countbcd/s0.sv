module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [2:0] ena,
    output logic [15:0] q
);

    logic ones_tc, tens_tc, hundreds_tc;
    logic [15:0] q_next;

    // Terminal-count signals for the lower three digits.
    assign ones_tc     = (q[3:0]  == 4'd9);
    assign tens_tc     = ones_tc && (q[7:4]  == 4'd9);
    assign hundreds_tc = tens_tc && (q[11:8] == 4'd9);

    // ena[0] enables tens, ena[1] enables hundreds, ena[2] enables thousands.
    assign ena[0] = ones_tc;
    assign ena[1] = tens_tc;
    assign ena[2] = hundreds_tc;

    // Next-state BCD count logic.
    always_comb begin
        if (!ones_tc) begin
            // Ones digit not terminal: increment ones only.
            q_next = {q[15:4], q[3:0] + 4'd1};
        end else if (!tens_tc) begin
            // Ones terminal, tens not terminal.
            q_next = {q[15:8], q[7:4] + 4'd1, 4'd0};
        end else if (!hundreds_tc) begin
            // Ones and tens terminal, hundreds not terminal.
            q_next = {q[15:12], q[11:8] + 4'd1, 4'd0, 4'd0};
        end else if (q[15:12] != 4'd9) begin
            // Ones, tens, and hundreds terminal, thousands not terminal.
            q_next = {q[15:12] + 4'd1, 4'd0, 4'd0, 4'd0};
        end else begin
            // All digits terminal: wrap from 9999 to 0000.
            q_next = 16'h0000;
        end
    end

    // Synchronous active-high reset.
    always_ff @(posedge clk) begin
        if (reset)
            q <= 16'h0000;
        else
            q <= q_next;
    end

endmodule
