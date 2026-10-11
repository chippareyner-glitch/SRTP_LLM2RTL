module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    input  logic ground,
    output logic walk_left,
    output logic walk_right,
    output logic aaah
);

    typedef enum logic [1:0] {
        WALK_L,
        WALK_R,
        FALL_L,
        FALL_R
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WALK_L;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            WALK_L: begin
                if (!ground)
                    next_state = FALL_L;
                else if (bump_left)
                    next_state = WALK_R;
                else
                    next_state = WALK_L;
            end
            WALK_R: begin
                if (!ground)
                    next_state = FALL_R;
                else if (bump_right)
                    next_state = WALK_L;
                else
                    next_state = WALK_R;
            end
            FALL_L: begin
                if (ground)
                    next_state = WALK_L;
                else
                    next_state = FALL_L;
            end
            FALL_R: begin
                if (ground)
                    next_state = WALK_R;
                else
                    next_state = FALL_R;
            end
            default: next_state = WALK_L;
        endcase
    end

    always_comb begin
        walk_left  = 1'b0;
        walk_right = 1'b0;
        aaah       = 1'b0;
        case (state)
            WALK_L: walk_left  = 1'b1;
            WALK_R: walk_right = 1'b1;
            FALL_L,
            FALL_R: aaah       = 1'b1;
            default: ;
        endcase
    end

endmodule
