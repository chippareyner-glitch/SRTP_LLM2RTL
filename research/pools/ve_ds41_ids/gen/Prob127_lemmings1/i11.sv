module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic {LEFT, RIGHT} state_t;
    state_t state, next_state;
    logic active;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state  <= LEFT;
            active <= 1'b0;
        end else begin
            state  <= next_state;
            active <= 1'b1;
        end
    end

    always_comb begin
        case (state)
            LEFT:    next_state = bump_left  ? RIGHT : LEFT;
            RIGHT:   next_state = bump_right ? LEFT  : RIGHT;
            default: next_state = LEFT;
        endcase
    end

    assign walk_left  = active && (state == LEFT);
    assign walk_right = active && (state == RIGHT);

endmodule
