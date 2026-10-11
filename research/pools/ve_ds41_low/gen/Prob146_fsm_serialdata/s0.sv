module TopModule(
  input  clk,
  input  in,
  input  reset,
  output logic [7:0] out_byte,
  output logic done
);

  typedef enum logic [1:0] {IDLE, DATA, STOP, WAIT} state_t;

  state_t     state;
  logic [7:0] data;
  logic [2:0] cnt;

  always_ff @(posedge clk) begin
    if (reset) begin
      state    <= IDLE;
      data     <= 8'h00;
      cnt      <= 3'd0;
      out_byte <= 8'h00;
      done     <= 1'b0;
    end else begin
      done <= 1'b0;

      case (state)
        // Idle line is 1; a 0 marks the start bit.
        IDLE: begin
          if (!in) state <= DATA;
        end

        // Shift in 8 data bits, LSB first.
        DATA: begin
          data <= {in, data[7:1]};
          if (cnt == 3'd7) begin
            cnt   <= 3'd0;
            state <= STOP;
          end else begin
            cnt <= cnt + 3'd1;
          end
        end

        // Verify stop bit.
        STOP: begin
          if (in) begin
            out_byte <= data;
            done     <= 1'b1;
            state    <= IDLE;
          end else begin
            // Bad stop bit: wait until a 1 appears before next byte.
            state <= WAIT;
          end
        end

        // Wait for the line to return to idle (1).
        WAIT: begin
          if (in) state <= IDLE;
        end
      endcase
    end
  end

endmodule
