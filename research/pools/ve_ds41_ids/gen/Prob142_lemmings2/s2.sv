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
        WL,
        WR,
        FL,
        FR
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WL;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            WL: begin
                if (!ground)
                    next_state = FL;
                else if (bump_left)
                    next_state = WR;
                else
                    next_state = WL;
            end
            WR: begin
                if (!ground)
                    next_state = FR;
                else if (bump_right)
                    next_state = WL;
                else
                    next_state = WR;
            end
            FL: begin
                if (ground)
                    next_state = WL;
                else
                    next_state = FL;
            end
            FR: begin
                if (ground)
                    next_state = WR;
                else
                    next_state = FR;
            end
            default: next_state = WL;
        endcase
    end

    assign walk_left  = (state == WL);
    assign walk_right = (state == WR);
    assign aaah       = (state == FL || state == FR);

endmodule
