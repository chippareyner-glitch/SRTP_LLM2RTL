module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic done
);

    typedef enum logic [2:0] {
        IDLE,
        START,
        DATA,
        STOP,
        WAIT
    } state_t;

    state_t state, next_state;
    logic [3:0] cnt, next_cnt;
    logic next_done;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 4'd0;
            done  <= 1'b0;
        end else begin
            state <= next_state;
            cnt   <= next_cnt;
            done  <= next_done;
        end
    end

    always_comb begin
        next_state = state;
        next_cnt   = cnt;
        next_done  = 1'b0;

        case (state)
            IDLE: begin
                next_cnt = 4'd0;
                if (in == 1'b0)
                    next_state = START;
            end

            START: begin
                next_state = DATA;
                next_cnt   = 4'd1;
            end

            DATA: begin
                if (cnt == 4'd7) begin
                    next_state = STOP;
                    next_cnt   = 4'd8;
                end else begin
                    next_state = DATA;
                    next_cnt   = cnt + 4'd1;
                end
            end

            STOP: begin
                if (in == 1'b1) begin
                    next_state = IDLE;
                    next_done  = 1'b1;
                end else begin
                    next_state = WAIT;
                end
            end

            WAIT: begin
                if (in == 1'b1)
                    next_state = IDLE;
                else
                    next_state = WAIT;
            end

            default: begin
                next_state = IDLE;
                next_cnt   = 4'd0;
            end
        endcase
    end

endmodule
