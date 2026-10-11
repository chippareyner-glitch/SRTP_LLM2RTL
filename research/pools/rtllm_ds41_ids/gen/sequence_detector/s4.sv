module sequence_detector (
    input  logic clk,
    input  logic rst_n,
    input  logic data_in,
    output logic sequence_detected
);

    typedef enum logic [2:0] {
        IDLE,
        S1,
        S2,
        S3,
        S4
    } state_t;

    state_t state, next_state;

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
