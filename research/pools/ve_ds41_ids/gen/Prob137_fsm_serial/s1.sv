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
    logic [3:0] count, next_count;

    assign done = (state == STOP) && in;

    always_comb begin
        next_state = state;
        next_count = count;
        case (state)
            IDLE: begin
                if (in == 1'b0) begin
                    next_state = DATA;
                    next_count = 4'd0;
                end
            end
            DATA: begin
                if (count == 4'd7) begin
                    next_state = STOP;
                end else begin
                    next_count = count + 1'b1;
                end
            end
            STOP: begin
                if (in == 1'b1) begin
                    next_state = IDLE;
                end else begin
                    next_state = WAIT;
                end
            end
            WAIT: begin
                if (in == 1'b1) begin
                    next_state = IDLE;
                end
            end
            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            count <= 4'd0;
        end else begin
            state <= next_state;
            count <= next_count;
        end
    end

endmodule
