module TopModule(
    input clk,
    input areset,
    input bump_left,
    input bump_right,
    input ground,
    output logic walk_left,
    output logic walk_right,
    output logic aaah
);

    typedef enum logic [1:0] {
        LEFT,
        RIGHT,
        FALL_LEFT,
        FALL_RIGHT
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            LEFT: begin
                if (!ground) begin
                    next_state = FALL_LEFT;
                end else if (bump_left && bump_right) begin
                    next_state = RIGHT;
                end else if (bump_left) begin
                    next_state = RIGHT;
                end else if (bump_right) begin
                    next_state = LEFT;
                end else begin
                    next_state = LEFT;
                end
            end
            RIGHT: begin
                if (!ground) begin
                    next_state = FALL_RIGHT;
                end else if (bump_left && bump_right) begin
                    next_state = LEFT;
                end else if (bump_left) begin
                    next_state = RIGHT;
                end else if (bump_right) begin
                    next_state = LEFT;
                end else begin
                    next_state = RIGHT;
                end
            end
            FALL_LEFT: begin
                if (ground) begin
                    next_state = LEFT;
                end else begin
                    next_state = FALL_LEFT;
                end
            end
            FALL_RIGHT: begin
                if (ground) begin
                    next_state = RIGHT;
                end else begin
                    next_state = FALL_RIGHT;
                end
            end
            default: next_state = LEFT;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
        end else begin
            state <= next_state;
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_LEFT) || (state == FALL_RIGHT);

endmodule
