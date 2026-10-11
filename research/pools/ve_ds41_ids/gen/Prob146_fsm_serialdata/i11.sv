module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    localparam IDLE = 2'b00;
    localparam DATA = 2'b01;
    localparam STOP = 2'b10;
    localparam WAIT = 2'b11;

    logic [1:0] state, next_state;
    logic [2:0] cnt;
    logic [7:0] data;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 3'd0;
            data  <= 8'h00;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    if (in == 1'b0) cnt <= 3'd0;
                end
                DATA: begin
                    data <= {in, data[7:1]};
                    cnt  <= cnt + 3'd1;
                end
                default: begin
                    // no register updates in STOP or WAIT
                end
            endcase
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in == 1'b0) next_state = DATA;
                else            next_state = IDLE;
            end
            DATA: begin
                if (cnt == 3'd7) next_state = STOP;
                else             next_state = DATA;
            end
            STOP: begin
                if (in == 1'b1) next_state = IDLE;
                else            next_state = WAIT;
            end
            WAIT: begin
                if (in == 1'b1) next_state = IDLE;
                else            next_state = WAIT;
            end
            default: next_state = IDLE;
        endcase
    end

    assign done     = ((state == STOP) || (state == WAIT)) && (in == 1'b1);
    assign out_byte = data;

endmodule
