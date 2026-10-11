module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    input  ground,
    input  dig,
    output walk_left,
    output walk_right,
    output aaah,
    output digging
);

    localparam LEFT   = 3'd0,
               RIGHT  = 3'd1,
               FALL_L = 3'd2,
               FALL_R = 3'd3,
               DIG_L  = 3'd4,
               DIG_R  = 3'd5;

    reg [2:0] state, next_state;

    // Asynchronous active-high reset to walking left
    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= LEFT;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            LEFT: begin
                if      (!ground)    next_state = FALL_L;   // fall has highest priority
                else if (dig)        next_state = DIG_L;    // dig next
                else if (bump_left)  next_state = RIGHT;    // else switch direction
                else                 next_state = LEFT;
            end
            RIGHT: begin
                if      (!ground)    next_state = FALL_R;
                else if (dig)        next_state = DIG_R;
                else if (bump_right) next_state = LEFT;
                else                 next_state = RIGHT;
            end
            FALL_L: begin
                if (ground) next_state = LEFT;   // resume original direction
                else        next_state = FALL_L;
            end
            FALL_R: begin
                if (ground) next_state = RIGHT;
                else        next_state = FALL_R;
            end
            DIG_L: begin
                if (!ground) next_state = FALL_L; // dug through to the other side
                else         next_state = DIG_L;
            end
            DIG_R: begin
                if (!ground) next_state = FALL_R;
                else         next_state = DIG_R;
            end
            default: next_state = LEFT;
        endcase
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L)  || (state == DIG_R);

endmodule
