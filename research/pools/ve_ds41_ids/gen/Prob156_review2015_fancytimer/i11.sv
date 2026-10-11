module TopModule (
    input clk,
    input reset,
    input data,
    output reg [3:0] count,
    output reg counting,
    output reg done,
    input ack
);

    localparam SEARCH = 2'd0;
    localparam SHIFT  = 2'd1;
    localparam COUNT  = 2'd2;
    localparam DONE   = 2'd3;

    reg [1:0] state, next_state;
    reg [3:0] hist;
    reg [3:0] delay_reg;
    reg [1:0] bit_cnt;
    reg [3:0] remain;
    reg [9:0] sub_cnt;

    always @(*) begin
        next_state = state;
        case (state)
            SEARCH: begin
                if ({hist[2:0], data} == 4'b1101)
                    next_state = SHIFT;
            end
            SHIFT: begin
                if (bit_cnt == 2'd3)
                    next_state = COUNT;
            end
            COUNT: begin
                if (remain == 4'd0 && sub_cnt == 10'd999)
                    next_state = DONE;
            end
            DONE: begin
                if (ack)
                    next_state = SEARCH;
            end
            default: next_state = SEARCH;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= SEARCH;
            hist <= 4'b0000;
            delay_reg <= 4'b0000;
            bit_cnt <= 2'd0;
            remain <= 4'd0;
            sub_cnt <= 10'd0;
            count <= 4'd0;
            counting <= 1'b0;
            done <= 1'b0;
        end else begin
            state <= next_state;

            counting <= (state == COUNT);
            done <= (state == DONE);
            count <= (state == COUNT) ? remain : 4'd0;

            case (state)
                SEARCH: begin
                    if ({hist[2:0], data} == 4'b1101)
                        bit_cnt <= 2'd0;
                    hist <= {hist[2:0], data};
                end
                SHIFT: begin
                    delay_reg <= {delay_reg[2:0], data};
                    if (bit_cnt == 2'd3) begin
                        bit_cnt <= 2'd0;
                        remain <= {delay_reg[2:0], data};
                        sub_cnt <= 10'd0;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end
                COUNT: begin
                    if (sub_cnt == 10'd999) begin
                        sub_cnt <= 10'd0;
                        if (remain != 4'd0)
                            remain <= remain - 1'b1;
                    end else begin
                        sub_cnt <= sub_cnt + 1'b1;
                    end
                end
                DONE: begin
                    if (ack) begin
                        hist <= 4'b0000;
                        bit_cnt <= 2'd0;
                    end
                end
            endcase
        end
    end

endmodule
