module TopModule (
    input  clk,
    input  reset,
    input  in,
    output done
);

    localparam IDLE  = 2'd0,
               DATA  = 2'd1,
               STOP  = 2'd2,
               ERROR = 2'd3;

    reg [1:0] state, next_state;
    reg [3:0] cnt;

    // Next-state logic
    always @(*) begin
        case (state)
            IDLE :   next_state = in ? IDLE : DATA;   // wait for start bit (0)
            DATA :   next_state = (cnt == 4'd7) ? STOP : DATA; // 8 data bits
            STOP :   next_state = in ? IDLE : ERROR;  // stop bit (1)?
            ERROR:   next_state = in ? IDLE : ERROR;  // wait for a stop bit
            default: next_state = IDLE;
        endcase
    end

    // State and bit-counter registers (synchronous, active-high reset)
    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 4'd0;
        end else begin
            state <= next_state;
            if (state == IDLE)
                cnt <= 4'd0;          // clear counter while idle
            else if (state == DATA)
                cnt <= cnt + 4'd1;    // count received data bits
        end
    end

    // Byte correctly received: in STOP state with a valid stop bit (1)
    assign done = (state == STOP) && in;

endmodule
