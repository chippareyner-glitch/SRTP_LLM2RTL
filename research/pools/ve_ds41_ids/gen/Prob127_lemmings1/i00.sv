module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    output walk_left,
    output walk_right
);

    typedef enum logic {LEFT = 1'b0, RIGHT = 1'b1} state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= LEFT;
        else
            state <= next_state;
    end

    always_comb begin
        if (bump_left && bump_right) begin
            if (state == LEFT)
                next_state = RIGHT;
            else
                next_state = LEFT;
        end
        else if (bump_left) begin
            next_state = RIGHT;
        end
        else if (bump_right) begin
            next_state = LEFT;
        end
        else begin
            next_state = state;
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
