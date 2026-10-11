module TopModule (
    input clk,
    input reset,
    input [7:0] in,
    output logic done
);

    localparam SEARCH = 2'b00;
    localparam BYTE1  = 2'b01;
    localparam BYTE2  = 2'b10;
    localparam BYTE3  = 2'b11;

    logic [1:0] state, next_state;

    always_comb begin
        case (state)
            SEARCH: next_state = (in[3] == 1'b1) ? BYTE1 : SEARCH;
            BYTE1:  next_state = BYTE2;
            BYTE2:  next_state = BYTE3;
            BYTE3:  next_state = (in[3] == 1'b1) ? BYTE1 : SEARCH;
            default: next_state = SEARCH;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= SEARCH;
        end else begin
            state <= next_state;
        end
    end

    assign done = (state == BYTE3);

endmodule
