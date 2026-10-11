module TopModule (
    input clk,
    input reset,
    input in,
    output done
);

    localparam IDLE = 2'b00;
    localparam DATA = 2'b01;
    localparam STOP = 2'b10;
    localparam WAIT = 2'b11;

    reg [1:0] state, next_state;
    reg [3:0] cnt;
    reg done_reg;

    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt <= 4'd0;
            done_reg <= 1'b0;
        end else begin
            state <= next_state;
            if (state == DATA)
                cnt <= cnt + 1'b1;
            else if (state == IDLE)
                cnt <= 4'd0;

            if (state == STOP && in)
                done_reg <= 1'b1;
            else
                done_reg <= 1'b0;
        end
    end

    always @(*) begin
        case (state)
            IDLE:  next_state = in ? IDLE : DATA;
            DATA:  next_state = (cnt == 4'd7) ? STOP : DATA;
            STOP:  next_state = in ? IDLE : WAIT;
            WAIT:  next_state = in ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    assign done = done_reg;

endmodule
