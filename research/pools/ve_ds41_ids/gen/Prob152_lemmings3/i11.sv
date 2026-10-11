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

    localparam LEFT   = 3'd0,
               RIGHT  = 3'd1,
               FALL_L = 3'd2,
               FALL_R = 3'd3,
               DIG_L  = 3'd4,
               DIG_R  = 3'd5;

    reg [2:0] state, next_state;
    reg [3:0] out;   // registered Moore outputs {digging, aaah, walk_right, walk_left}

    // Next-state logic: fall > dig > direction switch
    always @(*) begin
        case (state)
            LEFT:    next_state = ground ? (dig ? DIG_L : (bump_left  ? RIGHT : LEFT )) : FALL_L;
            RIGHT:   next_state = ground ? (dig ? DIG_R : (bump_right ? LEFT  : RIGHT)) : FALL_R;
            FALL_L:  next_state = ground ? LEFT  : FALL_L;
            FALL_R:  next_state = ground ? RIGHT : FALL_R;
            DIG_L:   next_state = ground ? DIG_L : FALL_L;
            DIG_R:   next_state = ground ? DIG_R : FALL_R;
            default: next_state = LEFT;
        endcase
    end

    // Combinational Moore outputs derived from current state
    wire wl = (state == LEFT);
    wire wr = (state == RIGHT);
    wire ah = (state == FALL_L) || (state == FALL_R);
    wire dg = (state == DIG_L)  || (state == DIG_R);

    // State register and registered output stage (outputs delayed one cycle)
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
            out   <= 4'b0001;   // walk_left after reset
        end else begin
            state <= next_state;
            out   <= {dg, ah, wr, wl};
        end
    end

    assign walk_left  = out[0];
    assign walk_right = out[1];
    assign aaah       = out[2];
    assign digging    = out[3];

endmodule
