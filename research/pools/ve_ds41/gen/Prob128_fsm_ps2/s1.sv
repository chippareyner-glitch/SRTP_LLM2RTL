module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [7:0] in,
    output logic done
);

    typedef enum logic [1:0] {
        BYTE1,
        BYTE2,
        BYTE3,
        DONE
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            BYTE1: next_state = in[3] ? BYTE2 : BYTE1;
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = DONE;
            DONE:  next_state = in[3] ? BYTE2 : BYTE1;
            default: next_state = BYTE1;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= BYTE1;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        done = (state == DONE);
    end

endmodule
