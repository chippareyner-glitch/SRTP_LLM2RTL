module TopModule(
    input  logic clk,
    input  logic reset,
    input  logic data,
    output logic [3:0] count,
    output logic counting,
    output logic done,
    input  logic ack
);

    typedef enum logic [1:0] {
        SEARCH,
        GET_DELAY,
        COUNT,
        DONE
    } state_t;

    state_t state;

    logic [2:0] sr;
    logic [1:0] bit_cnt;
    logic [3:0] count_reg;
    logic [9:0] timer;

    assign count    = count_reg;
    assign counting = (state == COUNT);
    assign done     = (state == DONE);

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= SEARCH;
            sr        <= 3'b000;
            bit_cnt   <= 2'd0;
            count_reg <= 4'd0;
            timer     <= 10'd0;
        end else begin
            case (state)
                SEARCH: begin
                    if ({sr, data} == 4'b1101) begin
                        state     <= GET_DELAY;
                        count_reg <= 4'd0;
                        bit_cnt   <= 2'd0;
                    end
                    sr <= {sr[1:0], data};
                end

                GET_DELAY: begin
                    if (bit_cnt == 2'd3) begin
                        count_reg <= {count_reg[2:0], data};
                        timer     <= 10'd999;
                        bit_cnt   <= 2'd0;
                        state     <= COUNT;
                    end else begin
                        count_reg <= {count_reg[2:0], data};
                        bit_cnt   <= bit_cnt + 2'd1;
                    end
                end

                COUNT: begin
                    if (timer != 10'd0) begin
                        timer <= timer - 10'd1;
                    end else begin
                        if (count_reg != 4'd0) begin
                            count_reg <= count_reg - 4'd1;
                            timer     <= 10'd999;
                        end else begin
                            state <= DONE;
                        end
                    end
                end

                DONE: begin
                    if (ack) begin
                        state   <= SEARCH;
                        sr      <= 3'b000;
                        bit_cnt <= 2'd0;
                    end
                end

                default: begin
                    state <= SEARCH;
                end
            endcase
        end
    end

endmodule
