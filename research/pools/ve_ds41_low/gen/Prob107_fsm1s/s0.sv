module TopModule (
    input  clk,
    input  reset,
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
            B: next_state = in ? B : A;
            A: next_state = in ? A : B;
            default: next_state = B;
        endcase
    end

    // State register with active-high synchronous reset
    always @(posedge clk) begin
        if (reset)
            state <= B;
        else
            state <= next_state;
    end

    // Moore output logic
    assign out = (state == B) ? 1'b1 : 1'b0;

endmodule
