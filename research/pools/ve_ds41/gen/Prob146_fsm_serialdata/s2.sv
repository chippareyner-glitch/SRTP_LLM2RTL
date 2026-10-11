module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    localparam logic [1:0] IDLE = 2'd0,
                           DATA = 2'd1,
                           STOP = 2'd2,
                           WAIT = 2'd3;

    logic [1:0] state;
    logic [2:0] bit_cnt;   // counts the 8 received data bits (0..7)
    logic [7:0] data;      // shift register, LSB received first

    always_ff @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 3'd0;
            data    <= 8'd0;
        end
        else begin
            case (state)
                // Idle line is high; a low level marks the start bit
                IDLE: begin
                    if (~in) begin
                        state   <= DATA;
                        bit_cnt <= 3'd0;
                    end
                end

                // Shift in 8 data bits, least significant bit first
                DATA: begin
                    data <= {in, data[7:1]};
                    if (bit_cnt == 3'd7)
                        state <= STOP;
                    else
                        bit_cnt <= bit_cnt + 3'd1;
                end

                // Check the stop bit
                STOP: begin
                    if (in)
                        state <= IDLE;   // valid stop bit -> next byte
                    else
                        state <= WAIT;   // framing error -> wait for a '1'
                end

                // After an error, wait until the line goes high again
                WAIT: begin
                    if (in)
                        state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    // Byte is complete and the stop bit is present during the STOP state
    assign done     = (state == STOP) && in;
    assign out_byte = data;

endmodule
