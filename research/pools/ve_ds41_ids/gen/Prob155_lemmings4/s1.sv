module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    input  ground,
    input  dig,
    output wire walk_left,
    output wire walk_right,
    output wire aaah,
    output wire digging
);

    localparam LEFT    = 3'd0;
    localparam RIGHT   = 3'd1;
    localparam FALL_L  = 3'd2;
    localparam FALL_R  = 3'd3;
    localparam DIG_L   = 3'd4;
    localparam DIG_R   = 3'd5;
    localparam SPLAT   = 3'd6;

    logic [2:0] state, next_state;
    logic [4:0] cnt, next_cnt;

    always_comb begin
        next_state = state;
        next_cnt   = cnt;
        case (state)
            LEFT: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_cnt   = 5'd0;
                end else if (dig) begin
                    next_state = DIG_L;
                end else if (bump_left) begin
                    next_state = RIGHT;
                end
            end
            RIGHT: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_cnt   = 5'd0;
                end else if (dig) begin
                    next_state = DIG_R;
                end else if (bump_right) begin
                    next_state = LEFT;
                end
            end
            FALL_L: begin
                if (ground) begin
                    if (cnt > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = LEFT;
                end else begin
                    if (cnt < 5'd21)
                        next_cnt = cnt + 5'd1;
                    else
                        next_cnt = cnt;
                end
            end
            FALL_R: begin
                if (ground) begin
                    if (cnt > 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = RIGHT;
                end else begin
                    if (cnt < 5'd21)
                        next_cnt = cnt + 5'd1;
                    else
                        next_cnt = cnt;
                end
            end
            DIG_L: begin
                if (!ground) begin
                    next_state = FALL_L;
                    next_cnt   = 5'd0;
                end
            end
            DIG_R: begin
                if (!ground) begin
                    next_state = FALL_R;
                    next_cnt   = 5'd0;
                end
            end
            SPLAT: begin
                next_state = SPLAT;
            end
            default: begin
                next_state = LEFT;
            end
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
            cnt   <= 5'd0;
        end else begin
            state <= next_state;
            cnt   <= next_cnt;
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L)  || (state == DIG_R);

endmodule
