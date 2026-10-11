module TopModule (
    input  clock,
    input  a,
    output reg p,
    output reg q
);

    // p: level-sensitive latch, transparent while clock is high
    always @(*) begin
        if (clock)
            p = a;
    end

    // q: negative-edge-triggered flip-flop capturing p
    always @(negedge clock) begin
        q <= p;
    end

endmodule
