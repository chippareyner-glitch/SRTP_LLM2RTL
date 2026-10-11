module TopModule (
    input  clock,
    input  a,
    output logic p,
    output logic q
);

    // p is a level-sensitive latch, transparent when clock is high
    always_latch begin
        if (clock) p = a;
    end

    // q is a negative-edge triggered flip-flop capturing p
    always_ff @(negedge clock) begin
        q <= p;
    end

endmodule
