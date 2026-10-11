module pulse_detect (
    input  logic clk,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);

    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        GOT0  = 2'b01,
        GOT01 = 2'b10,
        GOT1  = 2'b11
    } state_t;

    state_t state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            data_out <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (data_in) state <= GOT1;
                    else         state <= GOT0;
                    data_out <= 1'b0;
                end
                GOT0: begin
                    if (data_in) state <= GOT01;
                    else         state <= GOT0;
                    data_out <= 1'b0;
                end
                GOT01: begin
                    if (data_in) begin
                        state    <= GOT1;
                        data_out <= 1'b0;
                    end else begin
                        state    <= GOT0;
                        data_out <= 1'b1;
                    end
                end
                GOT1: begin
                    if (data_in) state <= GOT1;
                    else         state <= GOT0;
                    data_out <= 1'b0;
                end
                default: begin
                    state    <= IDLE;
                    data_out <= 1'b0;
                end
            endcase
        end
    end

endmodule
