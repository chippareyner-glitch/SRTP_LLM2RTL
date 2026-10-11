module TopModule (
    input  clk,
    input  aresetn,
    input  x,
    output z
);

    typedef enum logic [1:0] {
        S0 = 2'b00,
        S1 = 2'b01,
        S2 = 2'b10
    } state_t;

    state_t state, next_state;

    // Negative edge triggered asynchronous reset (active low)
    always_ff @(posedge clk or negedge aresetn) begin
        if (!aresetn) begin
            // Reset state is unspecified; choosing S1 ('1' already seen)
            state <= S1;
        end else begin
            state <= next_state;
        end
    end

    // Next state logic
    always_comb begin
        case (state)
            S0: next_state = (x) ? S1 : S0;
            S1: next_state = (x) ? S1 : S2;
            S2: next_state = (x) ? S1 : S0;
            default: next_state = S0;
        endcase
    end

    // Mealy output logic
    assign z = (state == S2) && x;

endmodule
