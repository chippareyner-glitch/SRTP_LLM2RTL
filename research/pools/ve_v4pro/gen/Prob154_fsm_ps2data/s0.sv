module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [7:0]  in,
    output logic [23:0] out_bytes,
    output logic        done
);

    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        WAIT2 = 2'b01,
        WAIT3 = 2'b10
    } state_t;

    state_t state;
    logic [7:0] byte1;
    logic [7:0] byte2;
    logic complete;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            byte1     <= 8'h00;
            byte2     <= 8'h00;
            out_bytes <= 24'h000000;
            done      <= 1'b0;
            complete  <= 1'b0;
        end else begin
            done     <= complete;
            complete <= 1'b0;

            case (state)
                IDLE: begin
                    if (in[3]) begin
                        byte1 <= in;
                        state <= WAIT2;
                    end
                end

                WAIT2: begin
                    byte2 <= in;
                    state <= WAIT3;
                end

                WAIT3: begin
                    out_bytes <= {byte1, byte2, in};
                    complete  <= 1'b1;
                    state     <= IDLE;
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
