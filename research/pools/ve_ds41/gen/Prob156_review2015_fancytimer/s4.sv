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
        SEARCH     = 2'd0,
        READ_DELAY = 2'd1,
        COUNT      = 2'd2,
        DONE_WAIT  = 2'd3
    } state_t;

    state_t state;
    logic [3:0] shift;
    logic [3:0] delay;
    logic [1:0] bitcnt;
    logic [3:0] cur_delay;
    logic [9:0] subcount;
    logic counting_reg, done_reg;

    always_ff @(posedge clk) begin
        if (reset) begin
            state        <= SEARCH;
            shift        <= 4'b0;
            delay        <= 4'b0;
            bitcnt       <= 2'b0;
            cur_delay    <= 4'b0;
            subcount     <= 10'b0;
            counting_reg <= 1'b0;
            done_reg     <= 1'b0;
        end else begin
            case (state)
                SEARCH: begin
                    shift <= {shift[2:0], data};
                    if ({shift[2:0], data} == 4'b1101) begin
                        state  <= READ_DELAY;
                        bitcnt <= 2'b0;
                    end
                end
                READ_DELAY: begin
                    delay  <= {delay[2:0], data};
                    bitcnt <= bitcnt + 1'b1;
                    if (bitcnt == 2'd3) begin
                        state        <= COUNT;
                        cur_delay    <= {delay[2:0], data};
                        subcount     <= 10'b0;
                        counting_reg <= 1'b1;
                        done_reg     <= 1'b0;
                    end
                end
                COUNT: begin
                    if (subcount == 10'd999) begin
                        if (cur_delay == 4'd0) begin
                            state        <= DONE_WAIT;
                            counting_reg <= 1'b0;
                            done_reg     <= 1'b1;
                        end else begin
                            cur_delay <= cur_delay - 1'b1;
                            subcount  <= 10'b0;
                        end
                    end else begin
                        subcount <= subcount + 1'b1;
                    end
                end
                DONE_WAIT: begin
                    if (ack) begin
                        state    <= SEARCH;
                        done_reg <= 1'b0;
                    end
                end
                default: state <= SEARCH;
            endcase
        end
    end

    assign counting = counting_reg;
    assign done     = done_reg;
    assign count    = cur_delay;

endmodule
