module TopModule (
    input clk,
    input in,
    input reset,
    output [7:0] out_byte,
    output done
);

    localparam IDLE = 3'd0,
               DATA = 3'd1,
               STOP = 3'd2,
               DONE = 3'd3,
               WAIT = 3'd4;

    reg [2:0] state;
    reg [2:0] cnt;
    reg [7:0] data_reg;

    assign done = (state == DONE);
    assign out_byte = data_reg;

    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt <= 3'd0;
            data_reg <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    if (in == 0) begin
                        state <= DATA;
                        cnt <= 3'd0;
                    end
                end
                DATA: begin
                    data_reg <= {in, data_reg[7:1]};
                    if (cnt == 3'd7) begin
                        state <= STOP;
                    end else begin
                        cnt <= cnt + 1'b1;
                    end
                end
                STOP: begin
                    if (in == 1) begin
                        state <= DONE;
                    end else begin
                        state <= WAIT;
                    end
                end
                DONE: begin
                    if (in == 0) begin
                        state <= DATA;
                        cnt <= 3'd0;
                    end else begin
                        state <= IDLE;
                    end
                end
                WAIT: begin
                    if (in == 1) begin
                        state <= IDLE;
                    end else begin
                        state <= WAIT;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

endmodule
