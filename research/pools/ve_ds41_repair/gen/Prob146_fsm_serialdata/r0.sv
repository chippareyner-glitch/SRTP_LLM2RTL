module TopModule (
    input  clk,
    input  in,
    input  reset,
    output reg [7:0] out_byte,
    output reg done
);

    localparam IDLE = 2'd0,
               DATA = 2'd1,
               STOP = 2'd2,
               WAIT = 2'd3;

    reg [1:0] state;
    reg [3:0] cnt;

    always @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            cnt      <= 4'd0;
            out_byte <= 8'h00;
            done     <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    if (in == 1'b0) begin
                        state    <= DATA;
                        cnt      <= 4'd0;
                        out_byte <= 8'h00;
                    end
                end
                DATA: begin
                    out_byte <= {in, out_byte[7:1]};
                    if (cnt == 4'd7) begin
                        state <= STOP;
                    end else begin
                        cnt <= cnt + 1'b1;
                    end
                end
                STOP: begin
                    if (in == 1'b1) begin
                        done  <= 1'b1;
                        state <= IDLE;
                    end else begin
                        state <= WAIT;
                    end
                end
                WAIT: begin
                    if (in == 1'b1) begin
                        state <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
