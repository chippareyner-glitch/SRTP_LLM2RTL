module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] in,
    output logic       done
);

    typedef enum logic [1:0] {
        WAIT_FIRST,
        WAIT_SECOND,
        WAIT_THIRD,
        DONE
    } state_t;

    state_t state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= WAIT_FIRST;
        end else begin
            case (state)
                WAIT_FIRST: begin
                    if (in[3])
                        state <= WAIT_SECOND;
                    else
                        state <= WAIT_FIRST;
                end
                WAIT_SECOND: begin
                    state <= WAIT_THIRD;
                end
                WAIT_THIRD: begin
                    state <= DONE;
                end
                DONE: begin
                    if (in[3])
                        state <= WAIT_SECOND;
                    else
                        state <= WAIT_FIRST;
                end
                default: begin
                    state <= WAIT_FIRST;
                end
            endcase
        end
    end

    assign done = (state == DONE);

endmodule
