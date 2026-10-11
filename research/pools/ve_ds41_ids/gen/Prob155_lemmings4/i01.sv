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
        WL, WR, FL, FR, DL, DR, SPLAT
    } state_t;

    state_t state, next_state;
    logic [4:0] fall_count;

    always_ff @(posedge clk) begin
        if (areset) begin
            state <= WL;
            fall_count <= 5'd0;
        end else begin
            state <= next_state;
            case (state)
                FL, FR: begin
                    if (ground) fall_count <= 5'd0;
                    else if (fall_count < 5'd21) fall_count <= fall_count + 5'd1;
                    else fall_count <= 5'd21;
                end
                default: begin
                    if (next_state == FL || next_state == FR)
                        fall_count <= 5'd1;
                    else
                        fall_count <= 5'd0;
                end
            endcase
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            WL: begin
                if (!ground) next_state = FL;
                else if (dig) next_state = DL;
                else if (bump_left) next_state = WR;
            end
            WR: begin
                if (!ground) next_state = FR;
                else if (dig) next_state = DR;
                else if (bump_right) next_state = WL;
            end
            FL: begin
                if (ground) begin
                    if (fall_count > 5'd20) next_state = SPLAT;
                    else next_state = WL;
                end else begin
                    next_state = FL;
                end
            end
            FR: begin
                if (ground) begin
                    if (fall_count > 5'd20) next_state = SPLAT;
                    else next_state = WR;
                end else begin
                    next_state = FR;
                end
            end
            DL: begin
                if (!ground) next_state = FL;
                else next_state = DL;
            end
            DR: begin
                if (!ground) next_state = FR;
                else next_state = DR;
            end
            SPLAT: next_state = SPLAT;
            default: next_state = WL;
        endcase
    end

    always_comb begin
        walk_left = (state == WL);
        walk_right = (state == WR);
        aaah = (state == FL || state == FR);
        digging = (state == DL || state == DR);
    end

endmodule
