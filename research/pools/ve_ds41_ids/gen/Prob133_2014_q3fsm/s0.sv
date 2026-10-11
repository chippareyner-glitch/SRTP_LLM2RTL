module TopModule(
    input clk,
    input reset,
    input s,
    input w,
    output logic z
);
    localparam A = 3'd0,
               B = 3'd1,
               C = 3'd2,
               D = 3'd3,
               E = 3'd4,
               F = 3'd5,
               G = 3'd6;

    logic [2:0] state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
            z <= 1'b0;
        end else begin
            state <= next_state;
            z <= (state == E && ~w) || (state == F && w);
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            A: next_state = s ? B : A;
            B: next_state = w ? C : D;
            C: next_state = w ? E : F;
            D: next_state = w ? F : G;
            E: next_state = B;
            F: next_state = B;
            G: next_state = B;
            default: next_state = A;
        endcase
    end
endmodule
