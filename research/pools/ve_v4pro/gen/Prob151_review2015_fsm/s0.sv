module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic data,
    input  logic done_counting,
    input  logic ack,
    output logic shift_ena,
    output logic counting,
    output logic done
);
    typedef enum logic [3:0] {
        IDLE,
        SEEN1,
        SEEN11,
        SEEN110,
        SHIFT1,
        SHIFT2,
        SHIFT3,
        SHIFT4,
        COUNTING,
        DONE
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE:    next_state = data ? SEEN1 : IDLE;
            SEEN1:   next_state = data ? SEEN11 : IDLE;
            SEEN11:  next_state = data ? SEEN11 : SEEN110;
            SEEN110: next_state = data ? SHIFT1 : IDLE;
            SHIFT1:  next_state = SHIFT2;
            SHIFT2:  next_state = SHIFT3;
            SHIFT3:  next_state = SHIFT4;
            SHIFT4:  next_state = COUNTING;
            COUNTING: next_state = done_counting ? DONE : COUNTING;
            DONE:    next_state = ack ? IDLE : DONE;
            default: next_state = IDLE;
        endcase
    end

    always_comb begin
        shift_ena = 1'b0;
        counting  = 1'b0;
        done      = 1'b0;

        case (state)
            SHIFT1,
            SHIFT2,
            SHIFT3,
            SHIFT4: shift_ena = 1'b1;

            COUNTING: counting = 1'b1;

            DONE: done = 1'b1;

            default: ;
        endcase
    end
endmodule
