module TopModule(
    input  wire clk,
    input  wire areset,
    input  wire bump_left,
    input  wire bump_right,
    output wire walk_left,
    output wire walk_right
);

    typedef enum logic {LEFT, RIGHT} state_t;
    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            LEFT:  if (bump_left)  next_state = RIGHT;
            RIGHT: if (bump_right) next_state = LEFT;
            default: next_state = LEFT;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) state <= LEFT;
        else        state <= next_state;
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
