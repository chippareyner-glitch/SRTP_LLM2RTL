module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    logic state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b1; // state B
        else begin
            case (state)
                1'b1: state <= in ? 1'b1 : 1'b0; // B: 0->A, 1->B
                1'b0: state <= in ? 1'b0 : 1'b1; // A: 0->B, 1->A
                default: state <= 1'b1;
            endcase
        end
    end

    assign out = state;

endmodule
