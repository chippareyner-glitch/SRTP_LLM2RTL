module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    input  ground,
    input  dig,
    output logic walk_left,
    output logic walk_right,
    output logic aaah,
    output logic digging
);

    typedef enum logic [2:0] {
        LEFT,
        RIGHT,
        FALL_L,
        FALL_R,
        DIG_L,
        DIG_R
    } state_t;

    state_t state, next;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= LEFT;
        else
            state <= next;
    end

    always_comb begin
        next = state;

        case (state)
            LEFT: begin
                if (!ground)
                    next = FALL_L;
                else if (dig)
                    next = DIG_L;
                else if (bump_left)
                    next = RIGHT;
            end

            RIGHT: begin
                if (!ground)
                    next = FALL_R;
                else if (dig)
                    next = DIG_R;
                else if (bump_right)
                    next = LEFT;
            end

            FALL_L: begin
                if (ground)
                    next = LEFT;
            end

            FALL_R: begin
                if (ground)
                    next = RIGHT;
            end

            DIG_L: begin
                if (!ground)
                    next = FALL_L;
            end

            DIG_R: begin
                if (!ground)
                    next = FALL_R;
            end

            default: next = LEFT;
        endcase
    end

    always_comb begin
        walk_left  = 1'b0;
        walk_right = 1'b0;
        aaah       = 1'b0;
        digging    = 1'b0;

        case (state)
            LEFT: begin
                walk_left = 1'b1;
            end

            RIGHT: begin
                walk_right = 1'b1;
            end

            FALL_L, FALL_R: begin
                aaah = 1'b1;
            end

            DIG_L, DIG_R: begin
                digging = 1'b1;
            end

            default: begin
                walk_left  = 1'b0;
                walk_right = 1'b0;
                aaah       = 1'b0;
                digging    = 1'b0;
            end
        endcase
    end

endmodule
