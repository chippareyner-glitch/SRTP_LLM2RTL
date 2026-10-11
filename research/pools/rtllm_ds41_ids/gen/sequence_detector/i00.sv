module sequence_detector (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output reg  sequence_detected
);

    localparam [2:0] IDLE = 3'd0,
                     S1   = 3'd1,
                     S2   = 3'd2,
                     S3   = 3'd3,
                     S4   = 3'd4;

    reg [2:0] state;
    reg [2:0] next_state;

    // State register: asynchronous active-low reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    // Next-state logic for sequence 1001 with overlap detection
    always @(*) begin
        case (state)
            IDLE:    next_state = data_in ? S1 : IDLE;
            S1:      next_state = data_in ? S1 : S2;   // matched "1"
            S2:      next_state = data_in ? S1 : S3;   // matched "10"
            S3:      next_state = data_in ? S4 : IDLE; // matched "100"
            S4:      next_state = data_in ? S1 : S2;   // matched "1001"
            default: next_state = IDLE;
        endcase
    end

    // Moore output: asserted while in S4 (the cycle the fourth bit is sampled)
    always @(*) begin
        sequence_detected = (state == S4);
    end

endmodule
