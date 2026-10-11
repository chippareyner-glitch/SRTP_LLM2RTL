module TopModule(
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        DATA  = 2'b01,
        STOP  = 2'b10,
        ERROR = 2'b11
    } state_t;

    state_t state, next_state;
    logic [3:0] cnt;
    logic [7:0] data;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            cnt   <= 4'd0;
            data  <= 8'd0;
        end else begin
            state <= next_state;
            if (state == IDLE && in == 1'b0) begin
                cnt <= 4'd0;
            end else if (state == DATA) begin
                data <= {in, data[7:1]};
                cnt  <= cnt + 4'd1;
            end
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in == 1'b0) next_state = DATA;
            end
            DATA: begin
                if (cnt == 4'd7) next_state = STOP;
            end
            STOP: begin
                if (in == 1'b1) next_state = IDLE;
                else next_state = ERROR;
            end
            ERROR: begin
                if (in == 1'b1) next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == STOP && in == 1'b1);
    assign out_byte = data;

endmodule
