module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    input  logic ground,
    input  logic dig,
    output logic walk_left,
    output logic walk_right,
    output logic aaah,
    output logic digging
);

    typedef enum logic [2:0] {
        LEFT    = 3'd0,
        RIGHT   = 3'd1,
        FALL_L  = 3'd2,
        FALL_R  = 3'd3,
        DIG_L   = 3'd4,
        DIG_R   = 3'd5,
        SPLAT   = 3'd6
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_count;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
            fall_count <= 5'd0;
        end else begin
            state <= next_state;
            if (next_state == FALL_L || next_state == FALL_R) begin
                if (state == FALL_L || state == FALL_R)
                    fall_count <= fall_count + 5'd1;
                else
                    fall_count <= 5'd1;
            end else begin
                fall_count <= 5'd0;
            end
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            LEFT: begin
                if (!ground) next_state = FALL_L;
                else if (dig) next_state = DIG_L;
                else if (bump_left) next_state = RIGHT;
                else next_state = LEFT;
            end
            RIGHT: begin
                if (!ground) next_state = FALL_R;
                else if (dig) next_state = DIG_R;
                else if (bump_right) next_state = LEFT;
                else next_state = RIGHT;
            end
            FALL_L: begin
                if (ground) begin
                    if (fall_count > 5'd20) next_state = SPLAT;
                    else next_state = LEFT;
                end else next_state = FALL_L;
            end
            FALL_R: begin
                if (ground) begin
                    if (fall_count > 5'd20) next_state = SPLAT;
                    else next_state = RIGHT;
                end else next_state = FALL_R;
            end
            DIG_L: begin
                if (!ground) next_state = FALL_L;
                else next_state = DIG_L;
            end
            DIG_R: begin
                if (!ground) next_state = FALL_R;
                else next_state = DIG_R;
            end
            SPLAT: next_state = SPLAT;
            default: next_state = LEFT;
        endcase
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L)  || (state == DIG_R);

endmodule
