module TopModule (
    input  clk,
    input  areset,
    input  in,
    output out
);

    // State encoding
    localparam A = 1'b0;
    localparam B = 1'b1;

    reg state, next_state;

    // Next-state logic (Moore)
    always @(*) begin
        case (state)
            A: next_state = in ? A : B;
            B: next_state = in ? B : A;
            default: next_state = B;
        endcase
    end

    // State register with asynchronous reset to B
    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= B;
        else
            state <= next_state;
    end

    // Moore output: B -> 1, A -> 0
    assign out = state;

endmodule
