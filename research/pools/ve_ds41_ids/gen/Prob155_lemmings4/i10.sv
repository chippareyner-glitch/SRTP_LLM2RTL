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
        WL, // walk left
        WR, // walk right
        FL, // fall left
        FR, // fall right
        DL, // dig left
        DR, // dig right
        SP  // splatter
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_cnt;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WL;
            fall_cnt <= 5'd0;
        end else begin
            state <= next_state;
            if (state == FL || state == FR) begin
                if (fall_cnt < 5'd20)
                    fall_cnt <= fall_cnt + 5'd1;
                else
                    fall_cnt <= fall_cnt;
            end else begin
                fall_cnt <= 5'd0;
            end
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            WL, WR, DL, DR, FL, FR: begin
                if (!ground) begin
                    // fall, preserve direction
                    if (state == WL || state == DL || state == FL)
                        next_state = FL;
                    else
                        next_state = FR;
                end else begin
                    case (state)
                        WL: begin
                            if (dig)
                                next_state = DL;
                            else if (bump_left)
                                next_state = WR;
                            else
                                next_state = WL;
                        end
                        WR: begin
                            if (dig)
                                next_state = DR;
                            else if (bump_right)
                                next_state = WL;
                            else
                                next_state = WR;
                        end
                        DL: begin
                            next_state = DL;
                        end
                        DR: begin
                            next_state = DR;
                        end
                        FL: begin
                            if (fall_cnt >= 5'd20)
                                next_state = SP;
                            else
                                next_state = WL;
                        end
                        FR: begin
                            if (fall_cnt >= 5'd20)
                                next_state = SP;
                            else
                                next_state = WR;
                        end
                    endcase
                end
            end
            SP: begin
                next_state = SP;
            end
        endcase
    end

    assign walk_left = (state == WL);
    assign walk_right = (state == WR);
    assign aaah = (state == FL || state == FR);
    assign digging = (state == DL || state == DR);

endmodule
