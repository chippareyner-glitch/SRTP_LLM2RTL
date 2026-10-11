module fsm (
    input  IN,
    input  CLK,
    input  RST,
    output reg MATCH
);

    // State encoding: states represent the longest matched prefix of "10011"
    localparam [2:0] S0 = 3'd0, // no prefix / idle
                     S1 = 3'd1, // "1"
                     S2 = 3'd2, // "10"
                     S3 = 3'd3, // "100"
                     S4 = 3'd4; // "1001"

    reg [2:0] state;

    // Mealy-style next-state logic with a registered output.
    // MATCH is set on the clock edge following the occurrence of the
    // final "1" of the sequence "10011", so it is a registered output
    // appearing one cycle after the last bit of the sequence.
    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            state <= S0;
            MATCH <= 1'b0;
        end
        else begin
            case (state)
                S0: begin
                    state <= IN ? S1 : S0;
                    MATCH <= 1'b0;
                end
                S1: begin
                    state <= IN ? S1 : S2;
                    MATCH <= 1'b0;
                end
                S2: begin
                    state <= IN ? S1 : S3;
                    MATCH <= 1'b0;
                end
                S3: begin
                    state <= IN ? S4 : S0;
                    MATCH <= 1'b0;
                end
                S4: begin
                    if (IN) begin
                        // "10011" detected; overlap restart at "1"
                        state <= S1;
                        MATCH <= 1'b1;
                    end
                    else begin
                        // "10010"; longest suffix prefix is "10"
                        state <= S2;
                        MATCH <= 1'b0;
                    end
                end
                default: begin
                    state <= S0;
                    MATCH <= 1'b0;
                end
            endcase
        end
    end

endmodule
