module TopModule (
    input  clk,
    input  reset,
    input  data,
    input  done_counting,
    input  ack,
    output shift_ena,
    output counting,
    output done
);

    localparam S0       = 4'd0,
               S1       = 4'd1,
               S11      = 4'd2,
               S110     = 4'd3,
               SHIFT1   = 4'd4,
               SHIFT2   = 4'd5,
               SHIFT3   = 4'd6,
               SHIFT4   = 4'd7,
               COUNT    = 4'd8,
               DONE     = 4'd9;

    logic [3:0] state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;

        case (state)
            S0:      next_state = data ? S1 : S0;
            S1:      next_state = data ? S11 : S0;
            S11:     next_state = data ? S11 : S110;
            S110:    next_state = data ? SHIFT1 : S0;

            SHIFT1:  next_state = SHIFT2;
            SHIFT2:  next_state = SHIFT3;
            SHIFT3:  next_state = SHIFT4;
            SHIFT4:  next_state = COUNT;

            COUNT:   next_state = done_counting ? DONE : COUNT;
            DONE:    next_state = ack ? S0 : DONE;

            default: next_state = S0;
        endcase
    end

    assign shift_ena = (state == SHIFT1) ||
                       (state == SHIFT2) ||
                       (state == SHIFT3) ||
                       (state == SHIFT4);

    assign counting  = (state == COUNT);
    assign done      = (state == DONE);

endmodule
