module TopModule (
    input clk,
    input areset,
    input bump_left,
    input bump_right,
    input ground,
    input dig,
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
        DIG_R,
        SPLAT
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_count, next_fall_count;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
            fall_count <= 5'd0;
        end else begin
            state <= next_state;
            fall_count <= next_fall_count;
        end
    end

    always_comb begin
        next_state = state;
        next_fall_count = fall_count;

        case (state)
            LEFT: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_count = 5'd0;
                end else if (dig) begin
                    next_state = DIG_L;
                end else if (bump_left || bump_right) begin
                    next_state = RIGHT;
                end else begin
                    next_state = LEFT;
                end
            end

            RIGHT: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_count = 5'd0;
                end else if (dig) begin
                    next_state = DIG_R;
                end else if (bump_left || bump_right) begin
                    next_state = LEFT;
                end else begin
                    next_state = RIGHT;
                end
            end

            FALL_L: begin
                if (ground) begin
                    if (fall_count > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = LEFT;
                end else begin
                    next_state = FALL_L;
                    if (fall_count < 5'd21)
                        next_fall_count = fall_count + 5'd1;
                    else
                        next_fall_count = fall_count;
                end
            end

            FALL_R: begin
                if (ground) begin
                    if (fall_count > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = RIGHT;
                end else begin
                    next_state = FALL_R;
                    if (fall_count < 5'd21)
                        next_fall_count = fall_count + 5'd1;
                    else
                        next_fall_count = fall_count;
                end
            end

            DIG_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_count = 5'd0;
                end else begin
                    next_state = DIG_L;
                end
            end

            DIG_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_count = 5'd0;
                end else begin
                    next_state = DIG_R;
                end
            end

            SPLAT: begin
                next_state = SPLAT;
            end

            default: next_state = LEFT;
        endcase
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L) || (state == DIG_R);

endmodule
