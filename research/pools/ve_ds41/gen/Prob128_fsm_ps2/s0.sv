module TopModule(
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] in,
    output logic       done
);

    typedef enum logic [1:0] {
        SEARCH,
        BYTE2,
        BYTE3,
        DONE
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            SEARCH: next_state = in[3] ? BYTE2 : SEARCH;
            BYTE2:  next_state = BYTE3;
            BYTE3:  next_state = DONE;
            DONE:   next_state = in[3] ? BYTE2 : SEARCH;
            default: next_state = SEARCH;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= SEARCH;
        else
            state <= next_state;
    end

    assign done = (state == DONE);

endmodule
