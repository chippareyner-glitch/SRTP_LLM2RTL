module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic out
);

    localparam logic B = 1'b1;
    localparam logic A = 1'b0;

    logic state, next_state;

    always_comb begin
        case (state)
            B: next_state = in ? B : A;
            A: next_state = in ? A : B;
            default: next_state = B;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= B;
        else
            state <= next_state;
    end

    assign out = state;

endmodule
