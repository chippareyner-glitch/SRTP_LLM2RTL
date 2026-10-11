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

    typedef enum logic [2:0] {
        LEFT,
        RIGHT,
        FALL_L,
        FALL_R,
        DIG_L,
        DIG_R
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= LEFT;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            LEFT: begin
                if (!ground)
                    next_state = FALL_L;
                else if (dig)
                    next_state = DIG_L;
                else if (bump_left)
                    next_state = RIGHT;
                else
                    next_state = LEFT;
            end
            RIGHT: begin
                if (!ground)
                    next_state = FALL_R;
                else if (dig)
                    next_state = DIG_R;
                else if (bump_right)
                    next_state = LEFT;
                else
                    next_state = RIGHT;
            end
            FALL_L: begin
                if (ground)
                    next_state = LEFT;
                else
                    next_state = FALL_L;
            end
            FALL_R: begin
                if (ground)
                    next_state = RIGHT;
                else
                    next_state = FALL_R;
            end
            DIG_L: begin
                if (!ground)
                    next_state = FALL_L;
                else
                    next_state = DIG_L;
            end
            DIG_R: begin
                if (!ground)
                    next_state = FALL_R;
                else
                    next_state = DIG_R;
            end
            default: next_state = LEFT;
        endcase
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L) || (state == DIG_R);

endmodule
