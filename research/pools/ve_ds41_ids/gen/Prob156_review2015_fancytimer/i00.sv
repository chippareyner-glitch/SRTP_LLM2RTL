module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    output logic [3:0] count,
    output logic counting,
    output logic done,
    input  logic ack
);

    localparam logic [1:0] SEARCH = 2'd0;
    localparam logic [1:0] LOAD   = 2'd1;
    localparam logic [1:0] COUNT  = 2'd2;
    localparam logic [1:0] WAIT   = 2'd3;

    logic [1:0] state;
    logic [3:0] sr;
    logic [3:0] delay_reg;
    logic [1:0] bit_cnt;
    logic [3:0] remaining;
    logic [9:0] cycle_cnt;

    wire [3:0] next_sr = {sr[2:0], data};
    wire [3:0] next_delay = {delay_reg[2:0], data};

    assign counting = (state == COUNT);
    assign done = ~counting;
    assign count = (state == COUNT) ? remaining : 4'b0000;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= SEARCH;
            sr <= 4'b0000;
            delay_reg <= 4'b0000;
            bit_cnt <= 2'd0;
            remaining <= 4'b0000;
            cycle_cnt <= 10'd0;
        end else begin
            case (state)
                SEARCH: begin
                    sr <= next_sr;
                    if (next_sr == 4'b1101) begin
                        state <= LOAD;
                        bit_cnt <= 2'd0;
                        delay_reg <= 4'b0000;
                    end
                end

                LOAD: begin
                    if (bit_cnt == 2'd3) begin
                        state <= COUNT;
                        remaining <= next_delay;
                        cycle_cnt <= 10'd0;
                    end else begin
                        delay_reg <= next_delay;
                        bit_cnt <= bit_cnt + 2'd1;
                    end
                end

                COUNT: begin
                    if (cycle_cnt == 10'd999) begin
                        cycle_cnt <= 10'd0;
                        if (remaining == 4'd0) begin
                            state <= WAIT;
                        end else begin
                            remaining <= remaining - 4'd1;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 10'd1;
                    end
                end

                WAIT: begin
                    if (ack) begin
                        state <= SEARCH;
                        sr <= 4'b0000;
                        delay_reg <= 4'b0000;
                        bit_cnt <= 2'd0;
                        remaining <= 4'b0000;
                        cycle_cnt <= 10'd0;
                    end
                end

                default: state <= SEARCH;
            endcase
        end
    end

endmodule
