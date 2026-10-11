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
        WALK_LEFT,
        WALK_RIGHT,
        FALL_LEFT,
        FALL_RIGHT,
        DIG_LEFT,
        DIG_RIGHT,
        SPLAT
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_cnt, next_fall_cnt;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WALK_LEFT;
            fall_cnt <= 5'd0;
        end else begin
            state <= next_state;
            fall_cnt <= next_fall_cnt;
        end
    end

    always_comb begin
        next_state = state;
        next_fall_cnt = fall_cnt;

        case (state)
            WALK_LEFT: begin
                if (ground == 1'b0) begin
                    next_state = FALL_LEFT;
                    next_fall_cnt = 5'd1;
                end else if (dig == 1'b1) begin
                    next_state = DIG_LEFT;
                end else if (bump_left == 1'b1) begin
                    next_state = WALK_RIGHT;
                end
            end

            WALK_RIGHT: begin
                if (ground == 1'b0) begin
                    next_state = FALL_RIGHT;
                    next_fall_cnt = 5'd1;
                end else if (dig == 1'b1) begin
                    next_state = DIG_RIGHT;
                end else if (bump_right == 1'b1) begin
                    next_state = WALK_LEFT;
                end
            end

            DIG_LEFT: begin
                if (ground == 1'b0) begin
                    next_state = FALL_LEFT;
                    next_fall_cnt = 5'd1;
                end
            end

            DIG_RIGHT: begin
                if (ground == 1'b0) begin
                    next_state = FALL_RIGHT;
                    next_fall_cnt = 5'd1;
                end
            end

            FALL_LEFT: begin
                if (ground == 1'b1) begin
                    if (fall_cnt > 5'd20) begin
                        next_state = SPLAT;
                    end else begin
                        next_state = WALK_LEFT;
                    end
                    next_fall_cnt = 5'd0;
                end else begin
                    if (fall_cnt < 5'd21) begin
                        next_fall_cnt = fall_cnt + 5'd1;
                    end else begin
                        next_fall_cnt = 5'd21;
                    end
                end
            end

            FALL_RIGHT: begin
                if (ground == 1'b1) begin
                    if (fall_cnt > 5'd20) begin
                        next_state = SPLAT;
                    end else begin
                        next_state = WALK_RIGHT;
                    end
                    next_fall_cnt = 5'd0;
                end else begin
                    if (fall_cnt < 5'd21) begin
                        next_fall_cnt = fall_cnt + 5'd1;
                    end else begin
                        next_fall_cnt = 5'd21;
                    end
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

    assign walk_left  = (state == WALK_LEFT);
    assign walk_right = (state == WALK_RIGHT);
    assign aaah       = (state == FALL_LEFT) || (state == FALL_RIGHT);
    assign digging    = (state == DIG_LEFT) || (state == DIG_RIGHT);

endmodule
