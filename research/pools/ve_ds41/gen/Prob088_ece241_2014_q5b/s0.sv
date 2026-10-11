module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output wire z
);

    localparam [1:0] A = 2'b01;
    localparam [1:0] B = 2'b10;

    logic [1:0] state;
    logic [1:0] next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = x ? B : A;
            B: next_state = B;
            default: next_state = A;
        endcase
    end

    assign z = (state[0] & x) | (state[1] & ~x);

endmodule
