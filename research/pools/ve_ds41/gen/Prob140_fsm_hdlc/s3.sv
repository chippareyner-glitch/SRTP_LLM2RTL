module TopModule (
    input  clk,
    input  reset,
    input  in,
    output disc,
    output flag,
    output err
);

    typedef enum logic [3:0] {
        S0   = 4'd0,
        S1   = 4'd1,
        S2   = 4'd2,
        S3   = 4'd3,
        S4   = 4'd4,
        S5   = 4'd5,
        S6   = 4'd6,
        DISC = 4'd7,
        FLAG = 4'd8,
        ERR  = 4'd9
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            S0:   next_state = in ? S1 : S0;
            S1:   next_state = in ? S2 : S0;
            S2:   next_state = in ? S3 : S0;
            S3:   next_state = in ? S4 : S0;
            S4:   next_state = in ? S5 : S0;
            S5:   next_state = in ? S6 : DISC;
            S6:   next_state = in ? ERR : FLAG;
            DISC: next_state = in ? S1 : S0;
            FLAG: next_state = in ? S1 : S0;
            ERR:  next_state = in ? ERR : S0;
            default: next_state = S0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    assign disc = (state == DISC);
    assign flag = (state == FLAG);
    assign err  = (state == ERR);

endmodule
