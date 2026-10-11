module TopModule(
    input clk,
    input reset,
    input data,
    output [3:0] count,
    output reg counting,
    output reg done,
    input ack
);

    localparam S_SEARCH = 2'd0;
    localparam S_DELAY  = 2'd1;
    localparam S_COUNT  = 2'd2;
    localparam S_DONE   = 2'd3;

    reg [1:0] state;
    reg [3:0] sr;
    reg [3:0] delay_reg;
    reg [1:0] bitcnt;
    reg [3:0] count_reg;
    reg [9:0] cycle_cnt;

    assign count = count_reg;

    always @(posedge clk) begin
        if (reset) begin
            state <= S_SEARCH;
            sr <= 4'd0;
            delay_reg <= 4'd0;
            bitcnt <= 2'd0;
            count_reg <= 4'd0;
            cycle_cnt <= 10'd0;
            counting <= 1'b0;
            done <= 1'b0;
        end else begin
            case (state)
                S_SEARCH: begin
                    counting <= 1'b0;
                    done <= 1'b0;
                    if ({sr[2:0], data} == 4'b1101) begin
                        state <= S_DELAY;
                        sr <= 4'd0;
                        bitcnt <= 2'd0;
                        delay_reg <= 4'd0;
                    end else begin
                        sr <= {sr[2:0], data};
                    end
                end

                S_DELAY: begin
                    counting <= 1'b0;
                    done <= 1'b0;
                    if (bitcnt == 2'd3) begin
                        state <= S_COUNT;
                        delay_reg <= {delay_reg[2:0], data};
                        count_reg <= {delay_reg[2:0], data};
                        bitcnt <= 2'd0;
                        cycle_cnt <= 10'd0;
                        counting <= 1'b1;
                    end else begin
                        delay_reg <= {delay_reg[2:0], data};
                        bitcnt <= bitcnt + 2'd1;
                    end
                end

                S_COUNT: begin
                    counting <= 1'b1;
                    done <= 1'b0;
                    if (cycle_cnt == 10'd999) begin
                        cycle_cnt <= 10'd0;
                        if (count_reg == 4'd0) begin
                            state <= S_DONE;
                            counting <= 1'b0;
                            done <= 1'b1;
                        end else begin
                            count_reg <= count_reg - 4'd1;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 10'd1;
                    end
                end

                S_DONE: begin
                    counting <= 1'b0;
                    done <= 1'b1;
                    if (ack) begin
                        state <= S_SEARCH;
                        sr <= 4'd0;
                        bitcnt <= 2'd0;
                        delay_reg <= 4'd0;
                        count_reg <= 4'd0;
                        cycle_cnt <= 10'd0;
                        counting <= 1'b0;
                        done <= 1'b0;
                    end
                end

                default: begin
                    state <= S_SEARCH;
                    counting <= 1'b0;
                    done <= 1'b0;
                end
            endcase
        end
    end

endmodule
