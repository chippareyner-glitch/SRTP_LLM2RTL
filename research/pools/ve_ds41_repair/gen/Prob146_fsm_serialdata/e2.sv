module TopModule(
    input clk,
    input in,
    input reset,
    output [7:0] out_byte,
    output done
);

    parameter IDLE = 0, DATA = 1, STOP = 2, DONE = 3, WAIT = 4;
    reg [2:0] state, next_state;
    reg [7:0] data;
    reg [3:0] cnt;
    reg done_reg;

    always @(*) begin
        case (state)
            IDLE: next_state = in ? IDLE : DATA;
            DATA: next_state = (cnt == 7) ? STOP : DATA;
            STOP: next_state = in ? IDLE : WAIT;
            DONE: next_state = IDLE;
            WAIT: next_state = in ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt <= 0;
            data <= 0;
            done_reg <= 0;
        end else begin
            state <= next_state;
            if (state == IDLE && !in) begin
                cnt <= 0;
            end else if (state == DATA) begin
                cnt <= cnt + 1;
                data <= {in, data[7:1]};
            end
            done_reg <= (state == STOP && in);
        end
    end

    assign out_byte = data;
    assign done = done_reg;

endmodule
