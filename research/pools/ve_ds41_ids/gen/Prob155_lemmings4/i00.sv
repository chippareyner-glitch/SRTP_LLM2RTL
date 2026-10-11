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

    localparam WALK_LEFT  = 3'd0;
    localparam WALK_RIGHT = 3'd1;
    localparam FALL_LEFT  = 3'd2;
    localparam FALL_RIGHT = 3'd3;
    localparam DIG_LEFT   = 3'd4;
    localparam DIG_RIGHT  = 3'd5;
    localparam SPLAT      = 3'd6;

    logic [2:0] state, next_state;
    logic [4:0] fall_cnt, next_fall_cnt;

    always_comb begin
        next_state = state;
        next_fall_cnt = fall_cnt;
        case (state)
            WALK_LEFT: begin
                if (!ground) begin
                    next_state = FALL_LEFT;
                    next_fall_cnt = 5'd0;
                end else if (dig) begin
                    next_state = DIG_LEFT;
                end else if (bump_left) begin
                    next_state = WALK_RIGHT;
                end
            end
            WALK_RIGHT: begin
                if (!ground) begin
                    next_state = FALL_RIGHT;
                    next_fall_cnt = 5'd0;
                end else if (dig) begin
                    next_state = DIG_RIGHT;
                end else if (bump_right) begin
                    next_state = WALK_LEFT;
                end
            end
            FALL_LEFT: begin
                if (ground) begin
                    if (fall_cnt >= 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = WALK_LEFT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = FALL_LEFT;
                    if (fall_cnt < 5'd20)
                        next_fall_cnt = fall_cnt + 1'b1;
                    else
                        next_fall_cnt = fall_cnt;
                end
            end
            FALL_RIGHT: begin
                if (ground) begin
                    if (fall_cnt >= 5'd20)
                        next_state = SPLAT;
                    else
                        next_state = WALK_RIGHT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = FALL_RIGHT;
                    if (fall_cnt < 5'd20)
                        next_fall_cnt = fall_cnt + 1'b1;
                    else
                        next_fall_cnt = fall_cnt;
                end
            end
            DIG_LEFT: begin
                if (!ground) begin
                    next_state = FALL_LEFT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = DIG_LEFT;
                end
            end
            DIG_RIGHT: begin
                if (!ground) begin
                    next_state = FALL_RIGHT;
                    next_fall_cnt = 5'd0;
                end else begin
                    next_state = DIG_RIGHT;
                end
            end
            SPLAT: begin
                next_state = SPLAT;
                next_fall_cnt = 5'd0;
            end
            default: begin
                next_state = WALK_LEFT;
                next_fall_cnt = 5'd0;
            end
        endcase
    end

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WALK_LEFT;
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
            WALK_LEFT:  walk_left = 1'b1;
            WALK_RIGHT: walk_right = 1'b1;
            FALL_LEFT, FALL_RIGHT: aaah = 1'b1;
            DIG_LEFT, DIG_RIGHT: digging = 1'b1;
            default: ; // SPLAT
        endcase
    end

endmodule
