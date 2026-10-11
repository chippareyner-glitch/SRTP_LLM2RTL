module TopModule (
    input clk,
    input reset,
    input [2:0] s,
    output fr2,
    output fr1,
    output fr0,
    output dfr
);

    localparam LOW   = 2'b00;
    localparam MED   = 2'b01;
    localparam HIGH  = 2'b10;
    localparam ABOVE = 2'b11;

    reg [1:0] state, next_state;

    always @(*) begin
        case (s)
            3'b000: next_state = LOW;
            3'b001: next_state = MED;
            3'b011: next_state = HIGH;
            3'b111: next_state = ABOVE;
            default: next_state = LOW;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= LOW;
        end else begin
            state <= next_state;
        end
    end

    assign fr2 = (state == LOW);
    assign fr1 = (state == LOW) || (state == MED);
    assign fr0 = (state == LOW) || (state == MED) || (state == HIGH);
    assign dfr = (state == LOW) || (state < next_state);

endmodule
