module TopModule (
  input  logic       clk,
  input  logic       reset,
  input  logic [2:0] s,
  output logic       fr2,
  output logic       fr1,
  output logic       fr0,
  output logic       dfr
);

  logic [1:0] level;
  logic       dfr_state;

  always_ff @(posedge clk) begin
    if (reset) begin
      level     <= 2'd0;
      dfr_state <= 1'b1;
    end else begin
      case (s)
        3'b000: begin
          level     <= 2'd0;
          dfr_state <= 1'b1;
        end
        3'b001: begin
          level <= 2'd1;
          if (level == 2'd0)
            dfr_state <= 1'b1;
          else if (level > 2'd1)
            dfr_state <= 1'b0;
        end
        3'b011: begin
          level <= 2'd2;
          if (level < 2'd2)
            dfr_state <= 1'b1;
          else if (level > 2'd2)
            dfr_state <= 1'b0;
        end
        3'b111: begin
          level     <= 2'd3;
          dfr_state <= 1'b0;
        end
        default: begin
        end
      endcase
    end
  end

  always_comb begin
    case (level)
      2'd0: begin
        fr2 = 1'b1;
        fr1 = 1'b1;
        fr0 = 1'b1;
        dfr = 1'b1;
      end
      2'd1: begin
        fr2 = 1'b0;
        fr1 = 1'b1;
        fr0 = 1'b1;
        dfr = dfr_state;
      end
      2'd2: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b1;
        dfr = dfr_state;
      end
      2'd3: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
        dfr = 1'b0;
      end
      default: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
        dfr = 1'b0;
      end
    endcase
  end

endmodule
