module TopModule (
    input  clk,
    input  reset,
    input  data,
    output reg [3:0] count,
    output reg counting,
    output reg done,
    input  ack
);

    localparam SEARCH = 2'd0,
               SHIFT  = 2'd1,
               COUNT  = 2'd2,
               DONE   = 2'd3;

    reg [1:0] state;
    reg [3:0] sr;          // sequence-detection shift register
    reg [1:0] shcnt;       // counts the 4 delay bits
    reg [9:0] cnt1000;     // 0..999 sub-counter
    reg [3:0] remaining;   // remaining 1000-cycle blocks
    reg [3:0] delay_reg;   // delay value being shifted in

    always @(posedge clk) begin
        if (reset) begin
            state     <= SEARCH;
            sr        <= 4'd0;
            shcnt     <= 2'd0;
            cnt1000   <= 10'd0;
            remaining <= 4'd0;
            delay_reg <= 4'd0;
        end
        else begin
            case (state)
                SEARCH: begin
                    sr <= {sr[2:0], data};
                    if ({sr[2:0], data} == 4'b1101) begin
                        state <= SHIFT;
                        shcnt <= 2'd0;
                    end
                end

                SHIFT: begin
                    if (shcnt == 2'd3) begin
                        state     <= COUNT;
                        delay_reg <= {delay_reg[2:0], data};
                        remaining <= {delay_reg[2:0], data};
                        cnt1000   <= 10'd999;
                    end
                    else begin
                        shcnt     <= shcnt + 2'd1;
                        delay_reg <= {delay_reg[2:0], data};
                    end
                end

                COUNT: begin
                    if (cnt1000 == 10'd0) begin
                        if (remaining == 4'd0) begin
                            state <= DONE;
                        end
                        else begin
                            remaining <= remaining - 4'd1;
                            cnt1000   <= 10'd999;
                        end
                    end
                    else begin
                        cnt1000 <= cnt1000 - 10'd1;
                    end
                end

                DONE: begin
                    if (ack) begin
                        state <= SEARCH;
                        sr    <= 4'd0;
                        shcnt <= 2'd0;
                    end
                end

                default: state <= SEARCH;
            endcase
        end
    end

    always @(*) begin
        counting = (state == COUNT);
        done     = (state == DONE);
        count    = (state == COUNT) ? remaining : 4'd0;
    end

endmodule
