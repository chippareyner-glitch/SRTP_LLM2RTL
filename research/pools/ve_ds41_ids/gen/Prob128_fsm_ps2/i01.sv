module TopModule (
    input clk,
    input reset,
    input [7:0] in,
    output logic done
);

    typedef enum logic [1:0] {
        SEARCH,
        BYTE1,
        BYTE2
    } state_t;

    state_t state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= SEARCH;
            done  <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                SEARCH: begin
                    if (in[3])
                        state <= BYTE1;
                    else
                        state <= SEARCH;
                end
                BYTE1: begin
                    state <= BYTE2;
                end
                BYTE2: begin
                    state <= SEARCH;
                    done  <= 1'b1;
                end
                default: begin
                    state <= SEARCH;
                end
            endcase
        end
    end

endmodule
