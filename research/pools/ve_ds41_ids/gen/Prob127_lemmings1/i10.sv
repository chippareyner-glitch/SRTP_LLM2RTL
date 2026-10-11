module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic {LEFT = 1'b0, RIGHT = 1'b1} state_t;

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
        if (areset)
            state <= LEFT;
        else
            state <= next_state;
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
