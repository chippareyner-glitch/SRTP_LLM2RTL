module fsm (
    input  logic IN,
    input  logic CLK,
    input  logic RST,
    output logic MATCH
);

    typedef enum logic [2:0] {
        IDLE = 3'd0,
        S1   = 3'd1,
        S2   = 3'd2,
        S3   = 3'd3,
        S4   = 3'd4
    } state_t;

    state_t state, next_state;

    always_ff @(posedge CLK or posedge RST) begin
        if (RST) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE: next_state = IN ? S1 : IDLE;
            S1:   next_state = IN ? S1 : S2;
            S2:   next_state = IN ? S1 : S3;
            S3:   next_state = IN ? S4 : IDLE;
            S4:   next_state = IN ? S1 : IDLE;
            default: next_state = IDLE;
        endcase
    end

    always_comb begin
        if (RST) begin
            MATCH = 1'b0;
        end else begin
            MATCH = (state == S4 && IN == 1'b1) ? 1'b1 : 1'b0;
        end
    end

endmodule
