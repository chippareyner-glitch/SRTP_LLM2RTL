module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [7:0] in,
    output logic [23:0] out_bytes,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE = 2'b00,
        B1   = 2'b01,
        B2   = 2'b10,
        DONE = 2'b11
    } state_t;

    state_t state;
    logic [7:0] byte1, byte2;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            byte1     <= 8'h00;
            byte2     <= 8'h00;
            out_bytes <= 24'h000000;
            done      <= 1'b0;
        end else begin
            done <= (state == DONE);

            case (state)
                IDLE: begin
                    if (in[3]) begin
                        byte1 <= in;
                        state <= B1;
                    end
                end

                B1: begin
                    byte2 <= in;
                    state <= B2;
                end

                B2: begin
                    out_bytes <= {byte1, byte2, in};
                    state     <= DONE;
                end

                DONE: begin
                    if (in[3]) begin
                        byte1 <= in;
                        state <= B1;
                    end else begin
                        state <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
