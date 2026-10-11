module TopModule (
    input  clk,
    input  reset,
    input  in,
    output done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        STOP,
        WAIT
    } state_t;

    state_t state, next_state;
    logic [2:0] bit_cnt;
    logic done_r;

    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in == 1'b0) next_state = DATA;
            end
            DATA: begin
                if (bit_cnt == 3'd7) next_state = STOP;
                else next_state = DATA;
            end
            STOP: begin
                if (in == 1'b1) next_state = IDLE;
                else next_state = WAIT;
            end
            WAIT: begin
                if (in == 1'b1) next_state = IDLE;
                else next_state = WAIT;
            end
            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            bit_cnt <= 3'd0;
            done_r <= 1'b0;
        end else begin
            state <= next_state;

            if (state == IDLE && next_state == DATA) begin
                bit_cnt <= 3'd0;
            end else if (state == DATA) begin
                bit_cnt <= bit_cnt + 1'b1;
            end

            if (state == STOP && in == 1'b1) begin
                done_r <= 1'b1;
            end else begin
                done_r <= 1'b0;
            end
        end
    end

    assign done = done_r;

endmodule
