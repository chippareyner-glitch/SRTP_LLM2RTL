module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    output [3:0] count,
    output counting,
    output done,
    input  logic ack
);

    logic [3:0] count_reg;
    logic [9:0] cycle_cnt;
    logic [3:0] sr;
    logic [3:0] delay_shift;
    logic [1:0] bit_cnt;
    logic [1:0] state;

    localparam logic [1:0] S_SEARCH = 2'd0;
    localparam logic [1:0] S_READ   = 2'd1;
    localparam logic [1:0] S_COUNT  = 2'd2;
    localparam logic [1:0] S_DONE   = 2'd3;

    assign count    = count_reg;
    assign counting = (state == S_COUNT) && !reset;
    assign done     = (state == S_DONE)  && !reset;

    always_ff @(posedge clk) begin
        if (reset) begin
            state       <= S_SEARCH;
            sr          <= 4'b0;
            delay_shift <= 4'b0;
            bit_cnt     <= 2'd0;
            count_reg   <= 4'b0;
            cycle_cnt   <= 10'd0;
        end else begin
            case (state)
                S_SEARCH: begin
                    sr <= {sr[2:0], data};
                    if ({sr[2:0], data} == 4'b1101) begin
                        state       <= S_READ;
                        bit_cnt     <= 2'd0;
                        delay_shift <= 4'b0;
                    end
                end
                S_READ: begin
                    if (bit_cnt == 2'd3) begin
                        count_reg <= {delay_shift[2:0], data};
                        cycle_cnt <= 10'd0;
                        state     <= S_COUNT;
                        bit_cnt   <= 2'd0;
                    end else begin
                        delay_shift <= {delay_shift[2:0], data};
                        bit_cnt     <= bit_cnt + 1'b1;
                    end
                end
                S_COUNT: begin
                    if (cycle_cnt == 10'd999) begin
                        cycle_cnt <= 10'd0;
                        if (count_reg == 4'd0) begin
                            state <= S_DONE;
                        end else begin
                            count_reg <= count_reg - 1'b1;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 1'b1;
                    end
                end
                S_DONE: begin
                    if (ack) begin
                        state <= S_SEARCH;
                        sr    <= 4'b0;
                    end
                end
                default: state <= S_SEARCH;
            endcase
        end
    end

endmodule
