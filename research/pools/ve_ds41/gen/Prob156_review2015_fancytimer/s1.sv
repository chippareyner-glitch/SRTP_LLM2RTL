module TopModule(
  input  clk,
  input  reset,
  input  data,
  output reg [3:0] count,
  output reg       counting,
  output reg       done,
  input  ack
);

  localparam S_SEARCH = 2'd0,
             S_DELAY  = 2'd1,
             S_COUNT  = 2'd2,
             S_DONE   = 2'd3;

  reg [1:0] state;
  reg [3:0] sr;        // start-pattern shift register
  reg [2:0] bitcnt;    // counts the 4 delay bits
  reg [3:0] delay;     // captured delay value
  reg [3:0] cnt_val;   // remaining time in units of 1000 cycles
  reg [9:0] sub;       // 0..999 sub-counter

  wire [3:0] sr_next    = {sr[2:0], data};
  wire [3:0] delay_next = {delay[2:0], data};

  always @(posedge clk) begin
    if (reset) begin
      state    <= S_SEARCH;
      sr       <= 4'b0000;
      bitcnt   <= 3'd0;
      delay    <= 4'b0000;
      cnt_val  <= 4'b0000;
      sub      <= 10'd0;
      counting <= 1'b0;
      done     <= 1'b0;
      count    <= 4'b0000;
    end else begin
      case (state)

        S_SEARCH: begin
          sr <= sr_next;
          if (sr_next == 4'b1101) begin
            state  <= S_DELAY;
            bitcnt <= 3'd0;
          end
        end

        S_DELAY: begin
          delay <= delay_next;
          if (bitcnt == 3'd3) begin
            // 4 bits captured (MSB first) -> begin counting
            state    <= S_COUNT;
            counting <= 1'b1;
            cnt_val  <= delay_next;
            count    <= delay_next;
            sub      <= 10'd0;
          end else begin
            bitcnt <= bitcnt + 3'd1;
          end
        end

        S_COUNT: begin
          if (sub == 10'd999) begin
            sub <= 10'd0;
            if (cnt_val == 4'd0) begin
              // (delay+1)*1000 cycles elapsed
              state    <= S_DONE;
              counting <= 1'b0;
              done     <= 1'b1;
            end else begin
              cnt_val <= cnt_val - 4'd1;
              count   <= cnt_val - 4'd1;
            end
          end else begin
            sub <= sub + 10'd1;
          end
        end

        S_DONE: begin
          if (ack) begin
            state <= S_SEARCH;
            done  <= 1'b0;
            sr    <= 4'b0000;
            count <= 4'b0000;
          end
        end

        default: state <= S_SEARCH;

      endcase
    end
  end

endmodule
