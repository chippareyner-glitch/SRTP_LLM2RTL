module pulse_detect (
    input  logic clk,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);

    localparam logic [1:0] IDLE  = 2'b00;
    localparam logic [1:0] GOT0  = 2'b01;
    localparam logic [1:0] GOT01 = 2'b10;

    logic [1:0] state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            data_out <= 1'b0;
        end else begin
            data_out <= 1'b0;

            case (state)
                IDLE: begin
                    if (!data_in)
                        state <= GOT0;
                    else
                        state <= IDLE;
                end

                GOT0: begin
                    if (data_in)
                        state <= GOT01;
                    else
                        state <= GOT0;
                end

                GOT01: begin
                    if (!data_in) begin
                        state    <= GOT0;
                        data_out <= 1'b1;
                    end else begin
                        state <= IDLE;
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
