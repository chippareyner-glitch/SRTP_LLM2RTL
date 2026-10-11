module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    input  ground,
    input  dig,
    output walk_left,
    output walk_right,
    output aaah,
    output digging
);

    localparam [2:0] WL    = 3'd0,
                     WR    = 3'd1,
                     FL    = 3'd2,
                     FR    = 3'd3,
                     DL    = 3'd4,
                     DR    = 3'd5,
                     SPLAT = 3'd6;

    reg [2:0] state, next_state;
    reg [4:0] cnt;

    // Sequential element: state register and fall-duration counter
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WL;
            cnt   <= 5'd0;
        end else begin
            state <= next_state;
            if (next_state == FL || next_state == FR) begin
                if (state == FL || state == FR)
                    cnt <= (cnt < 5'd21) ? (cnt + 5'd1) : 5'd21; // saturating
                else
                    cnt <= 5'd1;                                  // first fall cycle
            end else begin
                cnt <= 5'd0;
            end
        end
    end

    // Combinational next-state logic
    always @(*) begin
        next_state = state;
        case (state)
            WL: begin
                if (!ground)                      next_state = FL;   // fall priority
                else if (dig)                     next_state = DL;   // dig next
                else if (bump_left || bump_right) next_state = WR;   // switch direction
                else                              next_state = WL;
            end
            WR: begin
                if (!ground)                      next_state = FR;
                else if (dig)                     next_state = DR;
                else if (bump_left || bump_right) next_state = WL;
                else                              next_state = WR;
            end
            FL: begin
                if (ground) next_state = (cnt > 5'd20) ? SPLAT : WL;
                else        next_state = FL;
            end
            FR: begin
                if (ground) next_state = (cnt > 5'd20) ? SPLAT : WR;
                else        next_state = FR;
            end
            DL: begin
                if (!ground) next_state = FL;   // dug through, now fall
                else         next_state = DL;
            end
            DR: begin
                if (!ground) next_state = FR;
                else         next_state = DR;
            end
            SPLAT: next_state = SPLAT;
            default: next_state = WL;
        endcase
    end

    // Moore outputs
    assign walk_left  = (state == WL);
    assign walk_right = (state == WR);
    assign aaah       = (state == FL) || (state == FR);
    assign digging    = (state == DL) || (state == DR);

endmodule
