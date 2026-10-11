module TopModule (
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
        DIG_L,
        DIG_R
    } state_t;

    state_t state, next;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
        end else begin
            state <= next;
        end
    end

    always_comb begin
        next = state;
        case (state)
            LEFT: begin
                if (!ground)       next = FALL_L;
                else if (dig)      next = DIG_L;
                else if (bump_left) next = RIGHT;
                else               next = LEFT;
            end
            RIGHT: begin
                if (!ground)        next = FALL_R;
                else if (dig)       next = DIG_R;
                else if (bump_right) next = LEFT;
                else                next = RIGHT;
            end
            FALL_L: begin
                if (ground) next = LEFT;
                else        next = FALL_L;
            end
            FALL_R: begin
                if (ground) next = RIGHT;
                else        next = FALL_R;
            end
            DIG_L: begin
                if (!ground) next = FALL_L;
                else         next = DIG_L;
            end
            DIG_R: begin
                if (!ground) next = FALL_R;
                else         next = DIG_R;
            end
            default: next = LEFT;
        endcase
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L)  || (state == DIG_R);

endmodule
