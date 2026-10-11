module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [7:0]  in,
    output logic [23:0] out_bytes,
    output logic        done
);

    typedef enum logic [1:0] {
        IDLE,
        GET2,
        GET3,
        DONE
    } state_t;

    state_t state;
    logic [23:0] msg;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            done      <= 1'b0;
            msg       <= 24'h0;
            out_bytes <= 24'h0;
        end else begin
            done <= (state == DONE);
            case (state)
                IDLE: begin
                    if (in[3]) begin
                        msg[23:16] <= in;
                        state      <= GET2;
                    end
                end
                GET2: begin
                    msg[15:8] <= in;
                    state     <= GET3;
                end
                GET3: begin
                    msg[7:0] <= in;
                    state    <= DONE;
                end
                DONE: begin
                    out_bytes <= msg;
                    if (in[3]) begin
                        msg[23:16] <= in;
                        state      <= GET2;
                    end else begin
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

endmodule
