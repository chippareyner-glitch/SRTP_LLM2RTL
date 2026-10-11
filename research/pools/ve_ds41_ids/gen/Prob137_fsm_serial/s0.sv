module TopModule (
  input  logic clk,
  input  logic reset,
  input  logic in,
  output logic done
);

  typedef enum logic [1:0] {
    IDLE,
    DATA,
    STOP,
    WAIT
  } state_t;

  state_t state, next_state;
  logic [2:0] count;

  always_ff @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      count <= 3'd0;
      done  <= 1'b0;
    end else begin
      state <= next_state;
      done  <= 1'b0;
      case (state)
        IDLE: begin
          if (in == 1'b0) begin
            count <= 3'd0;
          end
        end
        DATA: begin
          if (count == 3'd7) begin
            count <= 3'd0;
          end else begin
            count <= count + 1'b1;
          end
        end
        STOP: begin
          if (in == 1'b1) begin
            done <= 1'b1;
          end
        end
        WAIT: begin
          // no count change
        end
      endcase
    end
  end

  always_comb begin
    next_state = state;
    case (state)
      IDLE: begin
        if (in == 1'b0) next_state = DATA;
      end
      DATA: begin
        if (count == 3'd7) next_state = STOP;
      end
      STOP: begin
        if (in == 1'b1) next_state = IDLE;
        else next_state = WAIT;
      end
      WAIT: begin
        if (in == 1'b1) next_state = IDLE;
      end
    endcase
  end

endmodule
