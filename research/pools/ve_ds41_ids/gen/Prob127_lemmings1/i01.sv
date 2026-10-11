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
    logic areset_d;
    logic reset_pulse;

    // Synchronous edge detection for areset
    always_ff @(posedge clk) begin
        areset_d <= areset;
    end

    assign reset_pulse = areset & ~areset_d;

    // State register with edge-triggered reset
    always_ff @(posedge clk) begin
        if (reset_pulse) begin
            state <= LEFT;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic (Moore FSM)
    always_comb begin
        case (state)
            LEFT:  next_state = bump_left  ? RIGHT : LEFT;
            RIGHT: next_state = bump_right ? LEFT  : RIGHT;
            default: next_state = LEFT;
        endcase
    end

    // Moore outputs
    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
