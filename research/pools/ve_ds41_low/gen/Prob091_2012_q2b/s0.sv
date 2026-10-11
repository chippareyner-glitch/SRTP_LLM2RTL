module TopModule (
    input  [5:0] y,
    input        w,
    output       Y1,
    output       Y3
);

    // One-hot encoding:
    // y[0] = A, y[1] = B, y[2] = C, y[3] = D, y[4] = E, y[5] = F
    //
    // Next-state logic for y[1] (B):
    // B is entered only from A when w = 1.
    assign Y1 = y[0] & w;

    // Next-state logic for y[3] (D):
    // D is entered from B, C, E, and F when w = 0.
    assign Y3 = (y[1] | y[2] | y[4] | y[5]) & ~w;

endmodule
