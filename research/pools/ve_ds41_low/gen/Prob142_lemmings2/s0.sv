module TopModule(
  input  clk,
  input  areset,
  input  bump_left,
  input  bump_right,
  input  ground,
  output walk_left,
  output walk_right,
  output aaah
);

  localparam LEFT   = 2'd0;
  localparam RIGHT  = 2'd1;
  localparam FALL_L = 2'd2;
  localparam FALL_R = 2'd3;

  reg [1:0] state, next;

  always @(posedge clk or posedge areset) begin
    if (areset)
      state <= LEFT;
    else
      state <= next;
  end

  always @(*) begin
    case (state)
      LEFT: begin
        if (!ground)
          next = FALL_L;
        else if (bump_left | bump_right)
          next = RIGHT;
        else
          next = LEFT;
      end
      RIGHT: begin
        if (!ground)
          next = FALL_R;
        else if (bump_left | bump_right)
          next = LEFT;
        else
          next = RIGHT;
      end
      FALL_L: begin
        next = ground ? LEFT : FALL_L;
      end
      FALL_R: begin
        next = ground ? RIGHT : FALL_R;
      end
      default: next = LEFT;
    endcase
  end

  assign walk_left  = (state == LEFT);
  assign walk_right = (state == RIGHT);
  assign aaah       = (state == FALL_L) | (state == FALL_R);

endmodule
