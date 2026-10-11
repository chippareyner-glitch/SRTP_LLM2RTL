module TopModule(
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    input  logic ground,
    input  logic dig,
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
        DIGL,
        DIGR
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            LEFT: begin
                if (!ground)       next_state = FALL_L;
                else if (dig)      next_state = DIGL;
                else if (bump_left) next_state = RIGHT;
                else               next_state = LEFT;
            end
            RIGHT: begin
                if (!ground)        next_state = FALL_R;
                else if (dig)       next_state = DIGR;
                else if (bump_right) next_state = LEFT;
                else                next_state = RIGHT;
            end
            FALL_L: begin
                if (ground) next_state = LEFT;
                else        next_state = FALL_L;
            end
            FALL_R: begin
                if (ground) next_state = RIGHT;
                else        next_state = FALL_R;
            end
            DIGL: begin
                if (!ground) next_state = FALL_L;
                else         next_state = DIGL;
            end
            DIGR: begin
                if (!ground) next_state = FALL_R;
                else         next_state = DIGR;
            end
            default: next_state = LEFT;
        endcase
    end

    always_comb begin
        walk_left  = (state == LEFT);
        walk_right = (state == RIGHT);
        aaah       = (state == FALL_L) || (state == FALL_R);
        digging    = (state == DIGL)   || (state == DIGR);
    end

endmodule
