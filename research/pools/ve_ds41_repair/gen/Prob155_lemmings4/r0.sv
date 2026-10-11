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
        LEFT,
        RIGHT,
        FALL_L,
        FALL_R,
        DIG_L,
        DIG_R,
        SPLAT
    } state_t;

    state_t state;
    logic [4:0] fall_cnt;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state    <= LEFT;
            fall_cnt <= 5'd0;
        end else begin
            case (state)
                LEFT, RIGHT: begin
                    if (!ground) begin
                        fall_cnt <= 5'd1;
                        state    <= (state == LEFT) ? FALL_L : FALL_R;
                    end else if (dig) begin
                        fall_cnt <= 5'd0;
                        state    <= (state == LEFT) ? DIG_L : DIG_R;
                    end else begin
                        fall_cnt <= 5'd0;
                        if (state == LEFT) begin
                            state <= bump_left ? RIGHT : LEFT;
                        end else begin
                            state <= bump_right ? LEFT : RIGHT;
                        end
                    end
                end

                FALL_L, FALL_R: begin
                    if (ground) begin
                        if (fall_cnt > 5'd20) begin
                            fall_cnt <= 5'd0;
                            state    <= SPLAT;
                        end else begin
                            fall_cnt <= 5'd0;
                            state    <= (state == FALL_L) ? LEFT : RIGHT;
                        end
                    end else begin
                        if (fall_cnt < 5'd31)
                            fall_cnt <= fall_cnt + 5'd1;
                        else
                            fall_cnt <= fall_cnt;
                        state <= state;
                    end
                end

                DIG_L, DIG_R: begin
                    if (!ground) begin
                        fall_cnt <= 5'd1;
                        state    <= (state == DIG_L) ? FALL_L : FALL_R;
                    end else begin
                        fall_cnt <= 5'd0;
                        state    <= state;
                    end
                end

                SPLAT: begin
                    fall_cnt <= 5'd0;
                    state    <= SPLAT;
                end

                default: begin
                    fall_cnt <= 5'd0;
                    state    <= LEFT;
                end
            endcase
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
    assign aaah       = (state == FALL_L) || (state == FALL_R);
    assign digging    = (state == DIG_L)  || (state == DIG_R);

endmodule
