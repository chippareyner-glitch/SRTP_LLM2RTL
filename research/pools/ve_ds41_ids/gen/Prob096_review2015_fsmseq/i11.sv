module TopModule (
    input clk,
    input reset,
    input data,
    output reg start_shifting
);

    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;
    localparam S3 = 2'b11;

    reg [1:0] state, next_state;

    initial begin
        state = S0;
        start_shifting = 1'b0;
    end

    always @(*) begin
        case (state)
            S0: next_state = data ? S1 : S0;
            S1: next_state = data ? S2 : S0;
            S2: next_state = data ? S2 : S3;
            S3: next_state = data ? S1 : S0;
            default: next_state = S0;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            start_shifting <= 1'b0;
        end else begin
            if (state == S3 && data == 1'b1)
                start_shifting <= 1'b1;
            state <= next_state;
        end
    end

endmodule
