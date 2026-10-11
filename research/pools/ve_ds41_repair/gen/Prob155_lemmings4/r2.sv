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
        WALK_L,
        WALK_R,
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
            state <= WALK_L;
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
            WALK_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_count = 5'd1;
                end else if (dig) begin
                    next_state = DIG_L;
                end else if (bump_left && bump_right) begin
                    next_state = WALK_R;
                end else if (bump_left) begin
                    next_state = WALK_R;
                end else if (bump_right) begin
                    next_state = WALK_L;
                end
            end

            WALK_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_count = 5'd1;
                end else if (dig) begin
                    next_state = DIG_R;
                end else if (bump_left && bump_right) begin
                    next_state = WALK_L;
                end else if (bump_left) begin
                    next_state = WALK_R;
                end else if (bump_right) begin
                    next_state = WALK_L;
                end
            end

            FALL_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    if (fall_count < 5'd21)
                        next_fall_count = fall_count + 5'd1;
                end else begin
                    if (fall_count > 5'd20) begin
                        next_state = SPLAT;
                        next_fall_count = 5'd0;
                    end else begin
                        next_state = WALK_L;
                        next_fall_count = 5'd0;
                    end
                end
            end

            FALL_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    if (fall_count < 5'd21)
                        next_fall_count = fall_count + 5'd1;
                end else begin
                    if (fall_count > 5'd20) begin
                        next_state = SPLAT;
                        next_fall_count = 5'd0;
                    end else begin
                        next_state = WALK_R;
                        next_fall_count = 5'd0;
                    end
                end
            end

            DIG_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_fall_count = 5'd1;
                end
            end

            DIG_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_fall_count = 5'd1;
                end
            end

            SPLAT: begin
                next_state = SPLAT;
                next_fall_count = 5'd0;
            end

            default: begin
                next_state = WALK_L;
                next_fall_count = 5'd0;
            end
        endcase
    end

    always_comb begin
        walk_left  = 1'b0;
        walk_right = 1'b0;
        aaah       = 1'b0;
        digging    = 1'b0;

        case (state)
            WALK_L: walk_left  = 1'b1;
            WALK_R: walk_right = 1'b1;
            FALL_L: aaah       = 1'b1;
            FALL_R: aaah       = 1'b1;
            DIG_L:  digging    = 1'b1;
            DIG_R:  digging    = 1'b1;
            default: ;
        endcase
    end

endmodule
