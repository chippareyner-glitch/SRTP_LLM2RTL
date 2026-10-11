module pulse_detect (
    input  logic clk,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);

    typedef enum logic [1:0] {
        IDLE = 2'b00,
        S1   = 2'b01,
        S2   = 2'b10
    } state_t;

    state_t state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            data_out <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (data_in == 1'b0) begin
                        state    <= S1;
                        data_out <= 1'b0;
                    end else begin
                        state    <= IDLE;
                        data_out <= 1'b0;
                    end
                end
                S1: begin
                    if (data_in == 1'b1) begin
                        state    <= S2;
                        data_out <= 1'b0;
                    end else begin
                        state    <= S1;
                        data_out <= 1'b0;
                    end
                end
                S2: begin
                    if (data_in == 1'b0) begin
                        state    <= S1;
                        data_out <= 1'b1;
                    end else begin
                        state    <= IDLE;
                        data_out <= 1'b0;
                    end
                end
                default: begin
                    state    <= IDLE;
                    data_out <= 1'b0;
                end
            endcase
        end
    end

endmodule
