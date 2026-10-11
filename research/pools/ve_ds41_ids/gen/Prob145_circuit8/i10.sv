module TopModule (
    input  clock,
    input  a,
    output reg p,
    output reg q
);

    // Level-sensitive latch: transparent while clock is high,
    // holds its value while clock is low.
    always @(*) begin
        if (clock)
            p = a;
    end

    // Falling-edge triggered flip-flop: captures p on the negedge of clock.
    always @(negedge clock) begin
        q <= p;
    end

endmodule
