module TopModule(
  input  logic clk,
  input  logic reset,
  input  logic in,
  output logic [7:0] out_byte,
  output logic done
);

  localparam logic [1:0] IDLE = 2'd0;
  localparam logic [1:0] DATA = 2'd1;
  localparam logic [1:0] STOP = 2'd2;
  localparam logic [1:0] WAIT = 2'd3;

  logic [1:0] state;
  logic [2:0] bit_cnt;
  logic [7:0] shift_reg;

  assign done = (state == STOP && in == 1);
  assign out_byte = shift_reg;

  always_ff @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      bit_cnt <= 3'd0;
      shift_reg <= 8'd0;
    end else begin
      case (state)
        IDLE: begin
          if (in == 0) begin
            state <= DATA;
            bit_cnt <= 3'd0;
          end else begin
            state <= IDLE;
          end
        end
        DATA: begin
          shift_reg[bit_cnt] <= in;
          if (bit_cnt == 3'd7) begin
            state <= STOP;
          end else begin
            bit_cnt <= bit_cnt + 3'd1;
            state <= DATA;
          end
        end
        STOP: begin
          if (in == 1) begin
            state <= IDLE;
          end else begin
            state <= WAIT;
          end
        end
        WAIT: begin
          if (in == 1) begin
            state <= IDLE;
          end else begin
            state <= WAIT;
          end
        end
        default: state <= IDLE;
      endcase
    end
  end

endmodule
