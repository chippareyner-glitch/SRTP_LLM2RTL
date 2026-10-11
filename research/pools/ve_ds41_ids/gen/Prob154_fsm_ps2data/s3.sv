module TopModule (
  input  logic       clk,
  input  logic       reset,
  input  logic [7:0] in,
  output logic [23:0] out_bytes,
  output logic       done
);

  typedef enum logic [1:0] {
    IDLE,
    BYTE2,
    BYTE3,
    DONE
  } state_t;

  state_t state;
  logic [7:0] byte1, byte2, byte3;

  always_ff @(posedge clk) begin
    if (reset) begin
      state     <= IDLE;
      done      <= 1'b0;
      out_bytes <= 24'h0;
      byte1     <= 8'h0;
      byte2     <= 8'h0;
      byte3     <= 8'h0;
    end else begin
      done <= 1'b0;
      case (state)
        IDLE: begin
          if (in[3]) begin
            byte1 <= in;
            state <= BYTE2;
          end
        end
        BYTE2: begin
          byte2 <= in;
          state <= BYTE3;
        end
        BYTE3: begin
          byte3 <= in;
          state <= DONE;
        end
        DONE: begin
          out_bytes <= {byte1, byte2, byte3};
          done      <= 1'b1;
          if (in[3]) begin
            byte1 <= in;
            state <= BYTE2;
          end else begin
            state <= IDLE;
          end
        end
        default: state <= IDLE;
      endcase
    end
  end

endmodule
