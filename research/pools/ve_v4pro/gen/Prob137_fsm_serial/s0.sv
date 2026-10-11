module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        WAIT_STOP,
        DONE
    } state_t;

    state_t state;
    logic [3:0] cnt;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 4'd0;
        end else begin
            case (state)
                IDLE: begin
                    cnt <= 4'd0;
                    if (in == 1'b0)
                        state <= DATA;   // start bit
                    else
                        state <= IDLE;
                end

                DATA: begin
                    if (cnt < 4'd8) begin
                        // Receiving one of the 8 data bits.
                        state <= DATA;
                        cnt   <= cnt + 4'd1;
                    end else begin
                        // Expected stop bit cycle.
                        cnt <= 4'd0;
                        if (in == 1'b1)
                            state <= DONE;
                        else
                            state <= WAIT_STOP;
                    end
                end

                WAIT_STOP: begin
                    cnt <= 4'd0;
                    if (in == 1'b1)
                        state <= IDLE;    // found a stop bit
                    else
                        state <= WAIT_STOP;
                end

                DONE: begin
                    cnt <= 4'd0;
                    // Next byte's start bit may arrive immediately.
                    if (in == 1'b0)
                        state <= DATA;
                    else
                        state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                    cnt   <= 4'd0;
                end
            endcase
        end
    end

    assign done = (state == DONE);

endmodule
