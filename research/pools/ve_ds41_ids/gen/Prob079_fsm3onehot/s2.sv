module TopModule (
    input  logic       in,
    input  logic [3:0] state,
    output logic [3:0] next_state,
    output logic       out
);

    logic sA, sB, sC, sD;

    assign sA = state[0];
    assign sB = state[1];
    assign sC = state[2];
    assign sD = state[3];

    assign next_state[0] = (~in) & (sA | sC);
    assign next_state[1] = in & (sA | sB | sD);
    assign next_state[2] = (~in) & (sB | sD);
    assign next_state[3] = in & sC;

    assign out = sD;

endmodule
