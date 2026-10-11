module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic {LEFT, RIGHT} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        if (bump_left && bump_right) begin
            next_state = (state == LEFT) ? RIGHT : LEFT;
        end else if (bump_left) begin
            next_state = RIGHT;
        end else if (bump_right) begin
            next_state = LEFT;
        end else begin
            next_state = state;
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
