module TopModule (
    input clk,
    input in,
    input reset,
    output [7:0] out_byte,
    output done
);

    typedef enum logic [3:0] {
        IDLE  = 4'd0,
        DATA0 = 4'd1,
        DATA1 = 4'd2,
        DATA2 = 4'd3,
        DATA3 = 4'd4,
        DATA4 = 4'd5,
        DATA5 = 4'd6,
        DATA6 = 4'd7,
        DATA7 = 4'd8,
        STOP  = 4'd9,
        WAIT  = 4'd10
    } state_t;

    state_t state, next_state;
    logic [7:0] data;

    always_comb begin
        next_state = state;
        case (state)
            IDLE:  if (in == 0) next_state = DATA0;
            DATA0: next_state = DATA1;
            DATA1: next_state = DATA2;
            DATA2: next_state = DATA3;
            DATA3: next_state = DATA4;
            DATA4: next_state = DATA5;
            DATA5: next_state = DATA6;
            DATA6: next_state = DATA7;
            DATA7: next_state = STOP;
            STOP:  if (in == 1) next_state = IDLE;
                   else next_state = WAIT;
            WAIT:  if (in == 1) next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            data <= 8'b0;
        end else begin
            state <= next_state;
            case (state)
                DATA0: data[0] <= in;
                DATA1: data[1] <= in;
                DATA2: data[2] <= in;
                DATA3: data[3] <= in;
                DATA4: data[4] <= in;
                DATA5: data[5] <= in;
                DATA6: data[6] <= in;
                DATA7: data[7] <= in;
            endcase
        end
    end

    assign out_byte = data;
    assign done = (state == STOP && in == 1);

endmodule
