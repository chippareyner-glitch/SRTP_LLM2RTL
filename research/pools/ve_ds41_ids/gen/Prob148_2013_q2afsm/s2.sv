module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic [2:0] r,
    output wire [2:0] g
);

    typedef enum logic [1:0] {
        S_A,
        S_B,
        S_C,
        S_D
    } state_t;

    state_t state, next_state;

    // State table / next-state logic
    always_comb begin
        next_state = state;
        case (state)
            S_A: begin
                if (r[0])       next_state = S_B;
                else if (r[1])  next_state = S_C;
                else if (r[2])  next_state = S_D;
                else            next_state = S_A;
            end
            S_B: begin
                if (r[0])       next_state = S_B;
                else            next_state = S_A;
            end
            S_C: begin
                if (r[1])       next_state = S_C;
                else            next_state = S_A;
            end
            S_D: begin
                if (r[2])       next_state = S_D;
                else            next_state = S_A;
            end
            default:            next_state = S_A;
        endcase
    end

    // State flip-flops with active-low synchronous reset
    always_ff @(posedge clk) begin
        if (!resetn)
            state <= S_A;
        else
            state <= next_state;
    end

    // Output logic (Moore)
    assign g[0] = (state == S_B);
    assign g[1] = (state == S_C);
    assign g[2] = (state == S_D);

endmodule
