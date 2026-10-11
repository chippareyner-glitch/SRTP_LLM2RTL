module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [7:0]  in,
    output logic [23:0] out_bytes,
    output logic        done
);

    typedef enum logic [1:0] {
        SEARCH,
        BYTE2,
        BYTE3,
        DONE
    } state_t;

    state_t state, next_state;
    logic [7:0] byte1, byte2;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= SEARCH;
            byte1 <= 8'h00;
            byte2 <= 8'h00;
            out_bytes <= 24'h000000;
        end else begin
            state <= next_state;
            case (state)
                SEARCH: begin
                    if (in[3]) begin
                        byte1 <= in;
                    end
                end
                BYTE2: begin
                    byte2 <= in;
                end
                BYTE3: begin
                    out_bytes <= {byte1, byte2, in};
                end
                DONE: begin
                    if (in[3]) begin
                        byte1 <= in;
                    end
                end
                default: begin
                end
            endcase
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            SEARCH: begin
                if (in[3]) next_state = BYTE2;
            end
            BYTE2: begin
                next_state = BYTE3;
            end
            BYTE3: begin
                next_state = DONE;
            end
            DONE: begin
                if (in[3]) next_state = BYTE2;
                else next_state = SEARCH;
            end
            default: begin
                next_state = SEARCH;
            end
        endcase
    end

    assign done = (state == DONE);

endmodule
