module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    logic [1:0] state, next_state;

    localparam A = 2'd0,
               B = 2'd1,
               C = 2'd2,
               D = 2'd3;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = x ? B : A;
            B: next_state = x ? D : C;
            C: next_state = x ? D : C;
            D: next_state = x ? D : C;
            default: next_state = A;
        endcase
    end

    assign z = (state == B) || (state == C);

endmodule
