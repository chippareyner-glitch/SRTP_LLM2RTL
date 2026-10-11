module TopModule(
    input clk,
    input reset,
    input [7:0] in,
    output done
);

    reg [1:0] state, next_state;

    localparam S0 = 2'd0,
               S1 = 2'd1,
               S2 = 2'd2,
               S3 = 2'd3;

    always @(*) begin
        case (state)
            S0: next_state = in[3] ? S1 : S0;
            S1: next_state = S2;
            S2: next_state = S3;
            S3: next_state = in[3] ? S1 : S0;
            default: next_state = S0;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            if (state == S2)
                state <= next_state;
            else
                state <= S0;
        end else begin
            state <= next_state;
        end
    end

    assign done = (state == S3);

endmodule
