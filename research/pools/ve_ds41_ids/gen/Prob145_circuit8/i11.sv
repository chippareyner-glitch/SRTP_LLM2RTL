module TopModule (
    input  clock,
    input  a,
    output logic p,
    output logic q
);

    logic a_sanitized;
    assign a_sanitized = (a === 1'b1) ? 1'b1 : 1'b0;

    always_latch begin
        if (clock) p = a_sanitized;
    end

    always_ff @(negedge clock) begin
        q <= p;
    end

endmodule
