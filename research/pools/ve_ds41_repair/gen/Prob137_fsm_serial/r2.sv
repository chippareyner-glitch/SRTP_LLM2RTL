module TopModule (
    input  clk,
    input  reset,
    input  in,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE  = 2'd0,
        DATA  = 2'd1,
        STOP  = 2'd2,
        ERROR = 2'd3
    } state_t;

    state_t state, next_state;
    logic [2:0] count, next_count;

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
                end else begin
                    next_count = count + 3'd1;
                end
            end

            STOP: begin
                if (in) begin
                    next_state = IDLE;
                end else begin
                    next_state = ERROR;
                end
            end

            ERROR: begin
                if (in) begin
                    next_state = IDLE;
                end
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            count <= 3'd0;
            done  <= 1'b0;
        end else begin
            state <= next_state;
            count <= next_count;

            if (state == STOP && in) begin
                done <= 1'b1;
            end else begin
                done <= 1'b0;
            end
        end
    end

endmodule
