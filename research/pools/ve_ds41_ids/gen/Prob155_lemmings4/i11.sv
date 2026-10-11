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

    localparam [2:0] WALK_L = 3'd0,
                     WALK_R = 3'd1,
                     DIG_L  = 3'd2,
                     DIG_R  = 3'd3,
                     FALL_L = 3'd4,
                     FALL_R = 3'd5,
                     SPLAT  = 3'd6;

    logic [2:0] state, next_state;
    logic [4:0] fall_count, next_fall_count;

    always_comb begin
        next_state = state;
        next_fall_count = fall_count;

        case (state)
            WALK_L: begin
                next_fall_count = 5'd0;
                if (!ground) begin
                    next_state = FALL_L;
                end else if (dig) begin
                    next_state = DIG_L;
                end else if (bump_left && bump_right) begin
                    next_state = WALK_R;
                end else if (bump_left) begin
                    next_state = WALK_R;
                end else if (bump_right) begin
                    next_state = WALK_L;
                end else begin
                    next_state = WALK_L;
                end
            end

            WALK_R: begin
                next_fall_count = 5'd0;
                if (!ground) begin
                    next_state = FALL_R;
                end else if (dig) begin
                    next_state = DIG_R;
                end else if (bump_left && bump_right) begin
                    next_state = WALK_L;
                end else if (bump_left) begin
                    next_state = WALK_R;
                end else if (bump_right) begin
                    next_state = WALK_L;
                end else begin
                    next_state = WALK_R;
                end
            end

            DIG_L: begin
                next_fall_count = 5'd0;
                if (!ground) begin
                    next_state = FALL_L;
                end else begin
                    next_state = DIG_L;
                end
            end

            DIG_R: begin
                next_fall_count = 5'd0;
                if (!ground) begin
                    next_state = FALL_R;
                end else begin
                    next_state = DIG_R;
                end
            end

            FALL_L: begin
                if (ground) begin
                    next_fall_count = 5'd0;
                    if (fall_count > 5'd20) begin
                        next_state = SPLAT;
                    end else begin
                        next_state = WALK_L;
                    end
                end else begin
                    next_state = FALL_L;
                    if (fall_count <= 5'd20) begin
                        next_fall_count = fall_count + 5'd1;
                    end else begin
                        next_fall_count = fall_count;
                    end
                end
            end

            FALL_R: begin
                if (ground) begin
                    next_fall_count = 5'd0;
                    if (fall_count > 5'd20) begin
                        next_state = SPLAT;
                    end else begin
                        next_state = WALK_R;
                    end
                end else begin
                    next_state = FALL_R;
                    if (fall_count <= 5'd20) begin
                        next_fall_count = fall_count + 5'd1;
                    end else begin
                        next_fall_count = fall_count;
                    end
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

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WALK_L;
            fall_count <= 5'd0;
        end else begin
            state <= next_state;
            fall_count <= next_fall_count;
        end
    end

    assign walk_left = (state == WALK_L);
    assign walk_right = (state == WALK_R);
    assign aaah = (state == FALL_L) || (state == FALL_R);
    assign digging = (state == DIG_L) || (state == DIG_R);

endmodule
