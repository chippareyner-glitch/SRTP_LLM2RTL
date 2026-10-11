module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;

    reg [1:0] state, next_state;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always @(*) begin
        case (state)
            S0: next_state = x ? S1 : S0;
            S1: next_state = x ? S2 : S1;
            S2: next_state = x ? S2 : S1;
            default: next_state = S0;
        endcase
    end

    assign z = (state == S1) ? 1'b1 : 1'b0;

endmodule
