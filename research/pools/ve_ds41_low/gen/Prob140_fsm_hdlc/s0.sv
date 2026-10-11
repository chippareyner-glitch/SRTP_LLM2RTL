module TopModule (
    input  clk,
    input  reset,
    input  in,
    output disc,
    output flag,
    output err
);

    typedef enum logic [3:0] {
        S0   = 4'd0,   // idle / previous input treated as 0
        S1   = 4'd1,   // one consecutive 1
        S2   = 4'd2,
        S3   = 4'd3,
        S4   = 4'd4,
        S5   = 4'd5,   // five consecutive 1s
        S6   = 4'd6,   // six consecutive 1s
        DISC = 4'd7,   // 0111110 -> discard
        FLAG = 4'd8,   // 01111110 -> flag
        ERR  = 4'd9    // 7 or more 1s -> error
    } state_t;

    state_t state, nextstate;

    always_ff @(posedge clk) begin
        if (reset) state <= S0;
        else       state <= nextstate;
    end

    always_comb begin
        case (state)
            S0:   nextstate = in ? S1   : S0;
            S1:   nextstate = in ? S2   : S0;
            S2:   nextstate = in ? S3   : S0;
            S3:   nextstate = in ? S4   : S0;
            S4:   nextstate = in ? S5   : S0;
            S5:   nextstate = in ? S6   : DISC;
            S6:   nextstate = in ? ERR  : FLAG;
            DISC: nextstate = in ? S1   : S0;
            FLAG: nextstate = in ? S1   : S0;
            ERR:  nextstate = in ? ERR  : S0;
            default: nextstate = S0;
        endcase
    end

    assign disc = (state == DISC);
    assign flag = (state == FLAG);
    assign err  = (state == ERR);

endmodule
