module TopModule (
    input clk,
    input reset,
    input [7:0] in,
    output logic done
);

    typedef enum logic [1:0] {
        S_SEARCH,
        S_BYTE2,
        S_BYTE3,
        S_DONE
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            S_SEARCH: begin
                if (in[3])
                    next_state = S_BYTE2;
                else
                    next_state = S_SEARCH;
            end
            S_BYTE2: begin
                next_state = S_BYTE3;
            end
            S_BYTE3: begin
                next_state = S_DONE;
            end
            S_DONE: begin
                next_state = S_SEARCH;
            end
            default: begin
                next_state = S_SEARCH;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= S_SEARCH;
        else
            state <= next_state;
    end

    assign done = (state == S_DONE);

endmodule
