module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    // One-hot encoded states
    reg [1:0] state;
    localparam A = 2'b01;
    localparam B = 2'b10;

    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else begin
            case (state)
                A: state <= x ? B : A;
                B: state <= B;
                default: state <= A;
            endcase
        end
    end

    // Mealy output: depends on current state and input x
    assign z = (state == A) ? x : ~x;

endmodule
