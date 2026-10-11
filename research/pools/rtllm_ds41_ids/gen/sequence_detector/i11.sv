module sequence_detector (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output wire sequence_detected
);

    localparam [2:0] IDLE = 3'd0,
                     S1   = 3'd1,
                     S2   = 3'd2,
                     S3   = 3'd3,
                     S4   = 3'd4;

    reg [2:0] state;
    reg [2:0] next_state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE:    next_state = data_in ? S1 : IDLE;
            S1:      next_state = data_in ? S1 : S2;
            S2:      next_state = data_in ? S1 : S3;
            S3:      next_state = data_in ? S4 : IDLE;
            S4:      next_state = data_in ? S1 : S2;
            default: next_state = IDLE;
        endcase
    end

    assign sequence_detected = (state == S4);

endmodule
