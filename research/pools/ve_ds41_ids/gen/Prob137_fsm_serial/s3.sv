module TopModule(
    input clk,
    input reset,
    input in,
    output done
);

    localparam IDLE = 2'd0;
    localparam DATA = 2'd1;
    localparam STOP = 2'd2;
    localparam WAIT = 2'd3;

    reg [1:0] state, next_state;
    reg [2:0] cnt;

    always @(*) begin
        case (state)
            IDLE:   next_state = (in == 1'b0) ? DATA : IDLE;
            DATA:   next_state = (cnt == 3'd7) ? STOP : DATA;
            STOP:   next_state = (in == 1'b1) ? IDLE : WAIT;
            WAIT:   next_state = (in == 1'b1) ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt <= 3'd0;
        end else begin
            state <= next_state;
            if (state == IDLE) begin
                cnt <= 3'd0;
            end else if (state == DATA) begin
                if (cnt == 3'd7)
                    cnt <= 3'd0;
                else
                    cnt <= cnt + 1'b1;
            end else begin
                cnt <= 3'd0;
            end
        end
    end

    assign done = (state == STOP) && (in == 1'b1);

endmodule
