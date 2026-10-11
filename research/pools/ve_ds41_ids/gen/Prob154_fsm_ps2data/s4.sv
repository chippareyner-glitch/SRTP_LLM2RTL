module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [7:0]  in,
    output logic [23:0] out_bytes,
    output logic        done
);

    localparam logic [1:0] IDLE = 2'd0;
    localparam logic [1:0] B1   = 2'd1;
    localparam logic [1:0] B2   = 2'd2;
    localparam logic [1:0] DONE = 2'd3;

    logic [1:0] state, next_state;
    logic [7:0] byte0, byte1, byte2;

    always_ff @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            done     <= 1'b0;
            out_bytes <= 24'b0;
            byte0    <= 8'b0;
            byte1    <= 8'b0;
            byte2    <= 8'b0;
        end else begin
            state <= next_state;
            done  <= (state == DONE);

            if (state == DONE) begin
                out_bytes <= {byte0, byte1, byte2};
            end

            case (state)
                IDLE: if (in[3]) byte0 <= in;
                B1:   byte1 <= in;
                B2:   byte2 <= in;
                DONE: if (in[3]) byte0 <= in;
                default: ;
            endcase
        end
    end

    always_comb begin
        case (state)
            IDLE: next_state = in[3] ? B1 : IDLE;
            B1:   next_state = B2;
            B2:   next_state = DONE;
            DONE: next_state = in[3] ? B1 : IDLE;
            default: next_state = IDLE;
        endcase
    end

endmodule
