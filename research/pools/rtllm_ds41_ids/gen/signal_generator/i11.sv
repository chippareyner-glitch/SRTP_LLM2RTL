module signal_generator (
    input  logic clk,
    input  logic rst_n,
    output logic [4:0] wave
);

    logic state;
    logic init_hold;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= 1'b0;
            wave      <= 5'd0;
            init_hold <= 1'b1;
        end else begin
            case (state)
                1'b0: begin
                    if (init_hold) begin
                        wave      <= 5'd0;
                        init_hold <= 1'b0;
                    end else if (wave == 5'd31) begin
                        wave  <= 5'd31;
                        state <= 1'b1;
                    end else begin
                        wave <= wave + 5'd1;
                    end
                end

                1'b1: begin
                    if (wave == 5'd0) begin
                        wave  <= 5'd0;
                        state <= 1'b0;
                    end else begin
                        wave <= wave - 5'd1;
                    end
                end
            endcase
        end
    end

endmodule
