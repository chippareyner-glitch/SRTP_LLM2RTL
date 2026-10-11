module pulse_detect (
    input  logic clk,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);

    localparam logic [1:0] S_IDLE  = 2'b00;
    localparam logic [1:0] S_SAW0  = 2'b01;
    localparam logic [1:0] S_SAW01 = 2'b10;

    logic [1:0] state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            data_out <= 1'b0;
        end else begin
            data_out <= 1'b0;

            case (state)
                S_IDLE: begin
                    if (!data_in)
                        state <= S_SAW0;
                    else
                        state <= S_IDLE;
                end

                S_SAW0: begin
                    if (data_in)
                        state <= S_SAW01;
                    else
                        state <= S_SAW0;
                end

                S_SAW01: begin
                    if (!data_in) begin
                        data_out <= 1'b1;
                        state    <= S_SAW0;
                    end else begin
                        state <= S_IDLE;
                    end
                end

                default: begin
                    state    <= S_IDLE;
                    data_out <= 1'b0;
                end
            endcase
        end
    end

endmodule
