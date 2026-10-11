module fsm (
    input  wire IN,
    input  wire CLK,
    input  wire RST,
    output wire MATCH
);

    localparam S0 = 3'd0,
               S1 = 3'd1,
               S2 = 3'd2,
               S3 = 3'd3,
               S4 = 3'd4;

    reg [2:0] state, next_state;

    always @(posedge CLK or posedge RST) begin
        if (RST)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S0: next_state = IN ? S1 : S0;
            S1: next_state = IN ? S1 : S2;
            S2: next_state = IN ? S1 : S3;
            S3: next_state = IN ? S4 : S0;
            S4: next_state = IN ? S1 : S2;
            default: next_state = S0;
        endcase
    end

    assign MATCH = (!RST && (state == S4) && IN) ? 1'b1 : 1'b0;

endmodule
