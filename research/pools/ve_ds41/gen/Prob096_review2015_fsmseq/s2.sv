module TopModule (
    input clk,
    input reset,
    input data,
    output start_shifting
);

    reg [2:0] state, next_state;

    localparam IDLE  = 3'd0,
               S1    = 3'd1,
               S11   = 3'd2,
               S110  = 3'd3,
               FOUND = 3'd4;

    always @(posedge clk) begin
        if (reset)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            IDLE:  next_state = data ? S1 : IDLE;
            S1:    next_state = data ? S11 : IDLE;
            S11:   next_state = data ? S11 : S110;
            S110:  next_state = data ? FOUND : IDLE;
            FOUND: next_state = FOUND;
            default: next_state = IDLE;
        endcase
    end

    assign start_shifting = (state == FOUND);

endmodule
