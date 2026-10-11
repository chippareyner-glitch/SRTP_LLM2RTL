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
    S_WALK_LEFT,
    S_WALK_RIGHT,
    S_FALL_LEFT,
    S_FALL_RIGHT,
    S_DIG_LEFT,
    S_DIG_RIGHT,
    S_SPLAT
  } state_t;

  state_t state, next_state;
  logic [4:0] fall_cnt;

  // Next state logic
  always_comb begin
    next_state = S_WALK_LEFT;
    case (state)
      S_WALK_LEFT: begin
        if (!ground)
          next_state = S_FALL_LEFT;
        else if (dig)
          next_state = S_DIG_LEFT;
        else if (bump_left)
          next_state = S_WALK_RIGHT;
        else
          next_state = S_WALK_LEFT;
      end

      S_WALK_RIGHT: begin
        if (!ground)
          next_state = S_FALL_RIGHT;
        else if (dig)
          next_state = S_DIG_RIGHT;
        else if (bump_right)
          next_state = S_WALK_LEFT;
        else
          next_state = S_WALK_RIGHT;
      end

      S_FALL_LEFT: begin
        if (ground) begin
          if (fall_cnt > 20)
            next_state = S_SPLAT;
          else
            next_state = S_WALK_LEFT;
        end else begin
          next_state = S_FALL_LEFT;
        end
      end

      S_FALL_RIGHT: begin
        if (ground) begin
          if (fall_cnt > 20)
            next_state = S_SPLAT;
          else
            next_state = S_WALK_RIGHT;
        end else begin
          next_state = S_FALL_RIGHT;
        end
      end

      S_DIG_LEFT: begin
        if (!ground)
          next_state = S_FALL_LEFT;
        else
          next_state = S_DIG_LEFT;
      end

      S_DIG_RIGHT: begin
        if (!ground)
          next_state = S_FALL_RIGHT;
        else
          next_state = S_DIG_RIGHT;
      end

      S_SPLAT: begin
        next_state = S_SPLAT;
      end

      default: begin
        next_state = S_WALK_LEFT;
      end
    endcase
  end

  // State and fall counter update
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state <= S_WALK_LEFT;
      fall_cnt <= 0;
    end else begin
      if ((state == S_FALL_LEFT) || (state == S_FALL_RIGHT)) begin
        if (!ground) begin
          if (fall_cnt < 21)
            fall_cnt <= fall_cnt + 1'b1;
        end else begin
          fall_cnt <= 0;
        end
      end else if ((next_state == S_FALL_LEFT) || (next_state == S_FALL_RIGHT)) begin
        fall_cnt <= 1;
      end else begin
        fall_cnt <= 0;
      end

      state <= next_state;
    end
  end

  // Moore outputs
  always_comb begin
    walk_left  = (state == S_WALK_LEFT);
    walk_right = (state == S_WALK_RIGHT);
    aaah       = (state == S_FALL_LEFT) || (state == S_FALL_RIGHT);
    digging    = (state == S_DIG_LEFT) || (state == S_DIG_RIGHT);
  end

endmodule
