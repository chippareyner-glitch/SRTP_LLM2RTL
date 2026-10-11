module TopModule (
    input  logic clk,
    input  logic aresetn,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {S0, S1, S2} state_t;
    state_t state, next;

    // Positive-edge triggered state update with negative-edge async reset
    always_ff @(posedge clk or negedge aresetn) begin
        if (!aresetn)
            state <= S0;
        else
            state <= next;
    end

    // Mealy next-state and output logic
    always_comb begin
        next = S0;
        z    = 1'b0;
        case (state)
            S0: begin
                if (x) next = S1;
                else   next = S0;
            end
            S1: begin
                if (x) next = S1;
                else   next = S2;
            end
            S2: begin
                if (x) begin
                    next = S1;   // overlapping: terminal 1 restarts detection
                    z    = 1'b1; // "101" detected
                end
                else begin
                    next = S0;
                end
            end
            default: begin
                next = S0;
                z    = 1'b0;
            end
        endcase
    end

endmodule
