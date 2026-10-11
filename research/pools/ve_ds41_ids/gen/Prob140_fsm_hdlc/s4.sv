module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic disc,
    output logic flag,
    output logic err
);

    typedef enum logic [3:0] {
        S0,
        S1,
        S2,
        S3,
        S4,
        S5,
        S6,
        DISC,
        FLAG,
        ERROR
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            S0:    next_state = in ? S1 : S0;
            S1:    next_state = in ? S2 : S0;
            S2:    next_state = in ? S3 : S0;
            S3:    next_state = in ? S4 : S0;
            S4:    next_state = in ? S5 : S0;
            S5:    next_state = in ? S6 : DISC;
            S6:    next_state = in ? ERROR : FLAG;
            DISC:  next_state = in ? S1 : S0;
            FLAG:  next_state = in ? S1 : S0;
            ERROR: next_state = in ? ERROR : S0;
            default: next_state = S0;
        endcase
    end

    assign disc = (state == DISC);
    assign flag = (state == FLAG);
    assign err  = (state == ERROR);

endmodule
