module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    output logic [3:0] count,
    output logic counting,
    output logic done,
    input  logic ack
);

    typedef enum logic [1:0] {
        S_SEARCH,
        S_GET_DELAY,
        S_COUNTING,
        S_DONE
    } state_t;

    state_t state;
    logic [3:0] hist;
    logic [3:0] delay_reg;
    logic [1:0] bit_cnt;
    logic [3:0] remaining;
    logic [9:0] cnt_1000;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= S_SEARCH;
            hist      <= 4'd0;
            delay_reg <= 4'd0;
            bit_cnt   <= 2'd0;
            remaining <= 4'd0;
            cnt_1000  <= 10'd0;
        end else begin
            case (state)
                S_SEARCH: begin
                    hist <= {hist[2:0], data};
                    if ({hist[2:0], data} == 4'b1101) begin
                        state   <= S_GET_DELAY;
                        bit_cnt <= 2'd0;
                    end
                end

                S_GET_DELAY: begin
                    delay_reg <= {delay_reg[2:0], data};
                    if (bit_cnt == 2'd3) begin
                        state     <= S_COUNTING;
                        remaining <= {delay_reg[2:0], data};
                        cnt_1000  <= 10'd0;
                    end else begin
                        bit_cnt <= bit_cnt + 2'd1;
                    end
                end

                S_COUNTING: begin
                    if (cnt_1000 == 10'd999) begin
                        cnt_1000 <= 10'd0;
                        if (remaining == 4'd0) begin
                            state <= S_DONE;
                        end else begin
                            remaining <= remaining - 4'd1;
                        end
                    end else begin
                        cnt_1000 <= cnt_1000 + 10'd1;
                    end
                end

                S_DONE: begin
                    if (ack) begin
                        state <= S_SEARCH;
                        hist  <= 4'd0;
                    end
                end

                default: state <= S_SEARCH;
            endcase
        end
    end

    assign counting = (state == S_COUNTING);
    assign done     = (state == S_DONE);
    assign count    = (state == S_COUNTING) ? remaining : 4'd0;

endmodule
