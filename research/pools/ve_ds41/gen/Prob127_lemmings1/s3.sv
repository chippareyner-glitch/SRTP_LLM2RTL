module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic {LEFT, RIGHT} state_t;
    state_t state, next;

    always_comb begin
        case (state)
            LEFT:  next = bump_left  ? RIGHT : LEFT;
            RIGHT: next = bump_right ? LEFT  : RIGHT;
            default: next = LEFT;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) state <= LEFT;
        else        state <= next;
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
