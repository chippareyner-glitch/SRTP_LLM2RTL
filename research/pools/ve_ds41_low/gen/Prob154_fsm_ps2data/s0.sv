module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [7:0] in,
    output logic [23:0] out_bytes,
    output logic done
);

    typedef enum logic [2:0] {
        IDLE,
        BYTE2,
        BYTE3,
        WAIT,
        DONE
    } state_t;

    state_t state, next_state;
    logic [7:0] byte1, byte2, byte3;
    logic [23:0] out_reg;
    logic new_msg;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            byte1 <= 8'h00;
            byte2 <= 8'h00;
            byte3 <= 8'h00;
            out_reg <= 24'h000000;
            new_msg <= 1'b0;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    if (in[3]) begin
                        byte1 <= in;
                    end
                end
                BYTE2: begin
                    byte2 <= in;
                end
                BYTE3: begin
                    byte3 <= in;
                    out_reg <= {byte1, byte2, in};
                end
                WAIT: begin
                    if (in[3]) begin
                        byte1 <= in;
                        new_msg <= 1'b1;
                    end else begin
                        new_msg <= 1'b0;
                    end
                end
                DONE: begin
                    new_msg <= 1'b0;
                end
            endcase
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in[3]) next_state = BYTE2;
                else next_state = IDLE;
            end
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = WAIT;
            WAIT: next_state = DONE;
            DONE: begin
                if (new_msg) next_state = BYTE2;
                else next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == DONE);
    assign out_bytes = out_reg;

endmodule
