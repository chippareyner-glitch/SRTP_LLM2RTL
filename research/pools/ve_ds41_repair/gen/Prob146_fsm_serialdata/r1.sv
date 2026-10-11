module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    typedef enum logic [2:0] {
        IDLE,
        START,
        DATA,
        STOP,
        WAIT
    } state_t;

    state_t state, next_state;
    logic [2:0] bit_cnt;
    logic [7:0] data_reg;
    logic done_reg;

    always_comb begin
        next_state = state;
        case (state)
            IDLE:  next_state = in ? IDLE : START;
            START: next_state = DATA;
            DATA:  next_state = (bit_cnt == 3'd7) ? STOP : DATA;
            STOP:  next_state = in ? IDLE : WAIT;
            WAIT:  next_state = in ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            bit_cnt  <= 3'd0;
            data_reg <= 8'd0;
            done_reg <= 1'b0;
        end else begin
            state    <= next_state;
            done_reg <= (state == STOP && in);

            if (state == IDLE && !in) begin
                bit_cnt <= 3'd0;
            end

            if (state == START) begin
                data_reg[0] <= in;
                bit_cnt     <= 3'd1;
            end

            if (state == DATA) begin
                data_reg[bit_cnt] <= in;
                if (bit_cnt == 3'd7) begin
                    bit_cnt <= 3'd0;
                end else begin
                    bit_cnt <= bit_cnt + 1'b1;
                end
            end
        end
    end

    assign out_byte = data_reg;
    assign done     = done_reg;

endmodule
