module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);
    localparam [3:0] IDLE      = 4'd0,
                     DATA0     = 4'd1,
                     DATA1     = 4'd2,
                     DATA2     = 4'd3,
                     DATA3     = 4'd4,
                     DATA4     = 4'd5,
                     DATA5     = 4'd6,
                     DATA6     = 4'd7,
                     DATA7     = 4'd8,
                     STOP      = 4'd9,
                     WAIT_STOP = 4'd10;

    logic [3:0] state, next_state;
    logic [7:0] shift_reg;

    always_comb begin
        next_state = state;
        case (state)
            IDLE:      next_state = in ? IDLE : DATA0;
            DATA0:     next_state = DATA1;
            DATA1:     next_state = DATA2;
            DATA2:     next_state = DATA3;
            DATA3:     next_state = DATA4;
            DATA4:     next_state = DATA5;
            DATA5:     next_state = DATA6;
            DATA6:     next_state = DATA7;
            DATA7:     next_state = STOP;
            STOP:      next_state = in ? IDLE : WAIT_STOP;
            WAIT_STOP: next_state = in ? IDLE : WAIT_STOP;
            default:   next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            shift_reg <= 8'b0;
        end else begin
            state <= next_state;
            case (state)
                DATA0: shift_reg <= {in, shift_reg[7:1]};
                DATA1: shift_reg <= {in, shift_reg[7:1]};
                DATA2: shift_reg <= {in, shift_reg[7:1]};
                DATA3: shift_reg <= {in, shift_reg[7:1]};
                DATA4: shift_reg <= {in, shift_reg[7:1]};
                DATA5: shift_reg <= {in, shift_reg[7:1]};
                DATA6: shift_reg <= {in, shift_reg[7:1]};
                DATA7: shift_reg <= {in, shift_reg[7:1]};
                default: shift_reg <= shift_reg;
            endcase
        end
    end

    assign out_byte = shift_reg;
    assign done = (state == STOP) && in;

endmodule
