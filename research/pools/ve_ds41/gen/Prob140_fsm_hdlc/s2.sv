module TopModule (
    input clk,
    input reset,
    input in,
    output logic disc,
    output logic flag,
    output logic err
);

    typedef enum logic [3:0] {
        S0, S1, S2, S3, S4, S5, S6, DISC, FLAG, ERR
    } state_t;

    state_t state, next;

    always_ff @(posedge clk) begin
        if (reset) state <= S0;
        else state <= next;
    end

    always_comb begin
        case (state)
            S0: next = in ? S1 : S0;
            S1: next = in ? S2 : S0;
            S2: next = in ? S3 : S0;
            S3: next = in ? S4 : S0;
            S4: next = in ? S5 : S0;
            S5: next = in ? S6 : DISC;
            S6: next = in ? ERR : FLAG;
            DISC: next = in ? S1 : S0;
            FLAG: next = in ? S1 : S0;
            ERR: next = ERR;
            default: next = S0;
        endcase
    end

    assign disc = (state == DISC);
    assign flag = (state == FLAG);
    assign err = (state == ERR);

endmodule
