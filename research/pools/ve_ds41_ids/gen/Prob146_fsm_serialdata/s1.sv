module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        DATA  = 2'b01,
        STOP  = 2'b10,
        WAIT  = 2'b11
    } state_t;

    state_t state, next_state;
    logic [3:0] bit_cnt;
    logic [7:0] data;

    // Sequential logic: state register, bit counter, and data shift register
    always_ff @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 4'd0;
            data    <= 8'd0;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    if (in == 1'b0) begin
                        bit_cnt <= 4'd0;
                    end
                end
                DATA: begin
                    data[bit_cnt] <= in;
                    bit_cnt <= bit_cnt + 1'b1;
                end
                STOP: begin
                    // no data update
                end
                WAIT: begin
                    // no data update
                end
            endcase
        end
    end

    // Combinational next-state logic
    always_comb begin
        case (state)
            IDLE: next_state = (in == 1'b0) ? DATA : IDLE;
            DATA: next_state = (bit_cnt == 4'd7) ? STOP : DATA;
            STOP: next_state = (in == 1'b1) ? IDLE : WAIT;
            WAIT: next_state = (in == 1'b1) ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    // Outputs
    assign done     = (state == STOP && in == 1'b1);
    assign out_byte = data;

endmodule
