module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] in,
    output logic       done
);

    typedef enum logic [1:0] {
        BYTE1,   // search for first byte: wait for in[3] == 1
        BYTE2,   // first byte received, expecting second byte
        BYTE3,   // second byte received, expecting third byte
        DONE     // third byte received
    } state_t;

    state_t state, next_state;

    // Next-state logic
    always_comb begin
        case (state)
            BYTE1:   next_state = in[3] ? BYTE2 : BYTE1;  // discard until in[3]==1
            BYTE2:   next_state = BYTE3;                  // accept second byte unconditionally
            BYTE3:   next_state = DONE;                   // accept third byte unconditionally
            DONE:    next_state = in[3] ? BYTE2 : BYTE1;  // this byte is byte1 of next msg
            default: next_state = BYTE1;
        endcase
    end

    // State register: positive-edge triggered, active-high synchronous reset
    always_ff @(posedge clk) begin
        if (reset)
            state <= BYTE1;
        else
            state <= next_state;
    end

    // done is asserted in the cycle immediately after the third byte is received
    assign done = (state == DONE);

endmodule
