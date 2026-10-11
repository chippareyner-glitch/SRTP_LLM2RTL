module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    localparam logic [1:0] IDLE = 2'd0,
                           DATA = 2'd1,
                           STOP = 2'd2,
                           WAIT = 2'd3;

    logic [1:0] state, next_state;
    logic [2:0] cnt;
    logic [7:0] data;

    always_comb begin
        case (state)
            IDLE: next_state = (in == 1'b0) ? DATA : IDLE;
            DATA: next_state = (cnt == 3'd7) ? STOP : DATA;
            STOP: next_state = (in == 1'b1) ? IDLE : WAIT;
            WAIT: next_state = (in == 1'b1) ? IDLE : WAIT;
            default: next_state = IDLE;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 3'd0;
            data  <= 8'd0;
        end else begin
            state <= next_state;
            if (state == IDLE && in == 1'b0) begin
                cnt <= 3'd0;
            end else if (state == DATA) begin
                data <= {in, data[7:1]};
                cnt  <= cnt + 1'b1;
            end
        end
    end

    assign done = (state == STOP && in == 1'b1);
    assign out_byte = data;

endmodule
