module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        STOP,
        ERROR
    } state_t;

    state_t state, next_state;
    logic [2:0] cnt;

    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 3'd0;
        end else begin
            state <= next_state;
            if (state == DATA) begin
                if (cnt == 3'd7)
                    cnt <= 3'd0;
                else
                    cnt <= cnt + 1'b1;
            end else if (state == IDLE) begin
                cnt <= 3'd0;
            end
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in == 1'b0)
                    next_state = DATA;
                else
                    next_state = IDLE;
            end
            DATA: begin
                if (cnt == 3'd7)
                    next_state = STOP;
                else
                    next_state = DATA;
            end
            STOP: begin
                if (in == 1'b1)
                    next_state = IDLE;
                else
                    next_state = ERROR;
            end
            ERROR: begin
                if (in == 1'b1)
                    next_state = IDLE;
                else
                    next_state = ERROR;
            end
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == STOP && in == 1'b1);

endmodule
