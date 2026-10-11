module pulse_detect (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output reg  data_out
);

    localparam S0 = 2'd0;  // waiting for the first 0
    localparam S1 = 2'd1;  // received first 0
    localparam S2 = 2'd2;  // received 0 then 1

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S0;
            data_out <= 1'b0;
        end else begin
            case (state)
                S0: begin
                    data_out <= 1'b0;
                    if (data_in == 1'b0)
                        state <= S1;
                    else
                        state <= S0;
                end

                S1: begin
                    data_out <= 1'b0;
                    if (data_in == 1'b1)
                        state <= S2;
                    else
                        state <= S1;
                end

                S2: begin
                    if (data_in == 1'b0) begin
                        data_out <= 1'b1;
                        state    <= S1;
                    end else begin
                        data_out <= 1'b0;
                        state    <= S0;
                    end
                end

                default: begin
                    state    <= S0;
                    data_out <= 1'b0;
                end
            endcase
        end
    end

endmodule
