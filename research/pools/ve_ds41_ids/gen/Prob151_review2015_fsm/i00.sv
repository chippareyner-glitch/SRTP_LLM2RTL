module TopModule (
    input clk,
    input reset,
    input data,
    input done_counting,
    input ack,
    output shift_ena,
    output counting,
    output done
);

    // State encoding
    localparam S    = 4'd0;
    localparam S1   = 4'd1;
    localparam S11  = 4'd2;
    localparam S110 = 4'd3;
    localparam B0   = 4'd4;
    localparam B1   = 4'd5;
    localparam B2   = 4'd6;
    localparam B3   = 4'd7;
    localparam COUNT= 4'd8;
    localparam WAIT = 4'd9;

    reg [3:0] state, next_state;

    // Next state logic
    always @(*) begin
        case (state)
            S:    next_state = data ? S1 : S;
            S1:   next_state = data ? S11 : S;
            S11:  next_state = data ? S11 : S110;
            S110: next_state = data ? B0 : S;
            B0:   next_state = B1;
            B1:   next_state = B2;
            B2:   next_state = B3;
            B3:   next_state = COUNT;
            COUNT:next_state = done_counting ? WAIT : COUNT;
            WAIT: next_state = ack ? S : WAIT;
            default: next_state = S;
        endcase
    end

    // State register with synchronous active-high reset
    always @(posedge clk) begin
        if (reset) begin
            state <= S;
        end else begin
            state <= next_state;
        end
    end

    // Output logic
    assign shift_ena = (state == B0 || state == B1 || state == B2 || state == B3);
    assign counting  = (state == COUNT);
    assign done      = (state == WAIT);

endmodule
