module TopModule (
    input  logic clk,
    input  logic aresetn,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        S0,
        S1,
        S2
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        z = 1'b0;

        case (state)
            S0: begin
                if (x)
                    next_state = S1;
                else
                    next_state = S0;
            end

            S1: begin
                if (x)
                    next_state = S1;
                else
                    next_state = S2;
            end

            S2: begin
                if (x) begin
                    next_state = S1;
                    z = 1'b1;
                end else begin
                    next_state = S0;
                end
            end

            default: begin
                next_state = S0;
                z = 1'b0;
            end
        endcase
    end

    always_ff @(posedge clk or negedge aresetn) begin
        if (!aresetn)
            state <= S0;
        else
            state <= next_state;
    end

endmodule
