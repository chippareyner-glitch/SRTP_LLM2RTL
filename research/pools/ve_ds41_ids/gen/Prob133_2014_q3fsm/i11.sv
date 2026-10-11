module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    typedef enum logic [2:0] {
        A, B, C, D, E
    } state_t;

    state_t state, next_state;
    logic [1:0] cnt;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
            cnt   <= 2'b00;
        end else begin
            state <= next_state;
            if (state == E)
                cnt <= 2'b00;
            else if ((state == B || state == C || state == D) && w)
                cnt <= cnt + 2'b01;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            A: next_state = s ? B : A;
            B: next_state = C;
            C: next_state = D;
            D: next_state = E;
            E: next_state = B;
            default: next_state = A;
        endcase
    end

    always_comb begin
        z = (state == E) && (cnt == 2'd2);
    end

endmodule
