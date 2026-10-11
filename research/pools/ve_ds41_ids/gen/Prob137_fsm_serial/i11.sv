module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic done
);

    typedef enum logic [2:0] {
        IDLE  = 3'd0,
        DATA  = 3'd1,
        STOP  = 3'd2,
        WAIT  = 3'd3,
        IDLE1 = 3'd4
    } state_t;

    state_t state, next_state;
    logic [2:0] cnt;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 3'd0;
        end else begin
            state <= next_state;
            if (state == IDLE && in == 1'b0)
                cnt <= 3'd0;
            else if (state == DATA)
                cnt <= cnt + 1'b1;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE:    if (in == 1'b0) next_state = DATA;
            DATA:    if (cnt == 3'd7) next_state = STOP;
            STOP:    if (in == 1'b1) next_state = IDLE1; else next_state = WAIT;
            WAIT:    if (in == 1'b1) next_state = IDLE;
            IDLE1:   if (in == 1'b1) next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == STOP) && (in == 1'b1);

endmodule
