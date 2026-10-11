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
        WAIT
    } state_t;

    state_t state, next_state;
    logic [3:0] bit_cnt;

    always_ff @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 4'd0;
        end else begin
            state <= next_state;
            if (state == DATA)
                bit_cnt <= bit_cnt + 1'b1;
            else
                bit_cnt <= 4'd0;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (!in) next_state = DATA;
            end
            DATA: begin
                if (bit_cnt == 4'd7) next_state = STOP;
            end
            STOP: begin
                if (!in) next_state = WAIT;
                else     next_state = IDLE;
            end
            WAIT: begin
                if (in) next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == STOP) && in;

endmodule
