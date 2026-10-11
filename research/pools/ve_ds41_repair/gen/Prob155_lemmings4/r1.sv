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
        DIG_L,
        DIG_R,
        FALL_L,
        FALL_R,
        SPLAT
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_cnt, next_fall_cnt;

    always_comb begin
        next_state = state;
        next_fall_cnt = 5'd0;

        case (state)
            LEFT: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_cnt = 5'd1;
                end else if (dig) begin
                    next_state = DIG_L;
                    next_fall_cnt = 5'd0;
                end else if (bump_left) begin
                    next_state = RIGHT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = LEFT;
                    next_fall_cnt = 5'd0;
                end
            end

            RIGHT: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_cnt = 5'd1;
                end else if (dig) begin
                    next_state = DIG_R;
                    next_fall_cnt = 5'd0;
                end else if (bump_right) begin
                    next_state = LEFT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = RIGHT;
                    next_fall_cnt = 5'd0;
                end
            end

            DIG_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_cnt = 5'd1;
                end else begin
                    next_state = DIG_L;
                    next_fall_cnt = 5'd0;
                end
            end

            DIG_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_cnt = 5'd1;
                end else begin
                    next_state = DIG_R;
                    next_fall_cnt = 5'd0;
                end
            end

            FALL_L: begin
                if (ground) begin
                    if (fall_cnt > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = LEFT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = FALL_L;
                    if (fall_cnt < 5'd21)
                        next_fall_cnt = fall_cnt + 5'd1;
                    else
                        next_fall_cnt = fall_cnt;
                end
            end

            FALL_R: begin
                if (ground) begin
                    if (fall_cnt > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = RIGHT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = FALL_R;
                    if (fall_cnt < 5'd21)
                        next_fall_cnt = fall_cnt + 5'd1;
                    else
                        next_fall_cnt = fall_cnt;
                end
            end

            SPLAT: begin
                next_state = SPLAT;
                next_fall_cnt = 5'd0;
            end

            default: begin
                next_state = LEFT;
                next_fall_cnt = 5'd0;
            end
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
            fall_cnt <= 5'd0;
        end else begin
            state <= next_state;
            fall_cnt <= next_fall_cnt;
        end
    end

    always_comb begin
        walk_left = 1'b0;
        walk_right = 1'b0;
        aaah = 1'b0;
        digging = 1'b0;

        case (state)
            LEFT:    walk_left = 1'b1;
            RIGHT:   walk_right = 1'b1;
            DIG_L:   digging = 1'b1;
            DIG_R:   digging = 1'b1;
            FALL_L:  aaah = 1'b1;
            FALL_R:  aaah = 1'b1;
            SPLAT:   begin
                walk_left = 1'b0;
                walk_right = 1'b0;
                aaah = 1'b0;
                digging = 1'b0;
            end
        endcase
    end

endmodule
