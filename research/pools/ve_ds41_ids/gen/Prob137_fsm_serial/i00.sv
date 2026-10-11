module TopModule (
    input  clk,
    input  reset,
    input  in,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE = 2'b00,
        DATA = 2'b01,
        STOP = 2'b10,
        WAIT = 2'b11
    } state_t;

    state_t state, next_state;
    logic [2:0] count, next_count;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            count <= 3'd0;
        end else begin
            state <= next_state;
            count <= next_count;
        end
    end

    always_comb begin
        next_state = state;
        next_count = count;
        case (state)
            IDLE: begin
                if (!in) begin
                    next_state = DATA;
                    next_count = 3'd0;
                end
            end
            DATA: begin
                if (count == 3'd7) begin
                    next_state = STOP;
                    next_count = 3'd0;
                end else begin
                    next_count = count + 3'd1;
                end
            end
            STOP: begin
                if (in) begin
                    next_state = IDLE;
                end else begin
                    next_state = WAIT;
                end
            end
            WAIT: begin
                if (in) begin
                    next_state = IDLE;
                end
            end
            default: begin
                next_state = IDLE;
                next_count = 3'd0;
            end
        endcase
    end

    assign done = (state == STOP) && in;

endmodule
