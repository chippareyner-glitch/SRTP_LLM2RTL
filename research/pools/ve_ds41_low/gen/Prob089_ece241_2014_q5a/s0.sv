module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    // Moore states for the serial 2's-complementer.
    //
    // The input bits arrive LSB first.  Until the first '1' arrives the bits
    // are simply copied; from then on every bit is inverted.  For a Moore
    // machine the output can only depend on the current state, so the output
    // bit for the incoming bit is produced on the following clock (inherent
    // one-cycle Moore latency).  The states remember both the phase and the
    // most recently received bit, which is exactly what the output needs.
    //
    //   A : no '1' has been received yet                       -> output 0
    //   B : first '1' was the last bit, or we are inverting
    //       with a '0' as the last bit                         -> output 1
    //   C : we are inverting and the last bit received is '1'  -> output 0

    typedef enum logic [1:0] {
        A = 2'd0,
        B = 2'd1,
        C = 2'd2
    } state_t;

    state_t state, next_state;

    // Moore output (function of the state only)
    assign z = (state == B) ? 1'b1 : 1'b0;

    // Next-state logic
    always @(*) begin
        case (state)
            A:       next_state = x ? B : A;
            B:       next_state = x ? C : B;
            C:       next_state = x ? C : B;
            default: next_state = A;
        endcase
    end

    // Positive-edge clock with asynchronous, active-high reset
    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= A;
        else
            state <= next_state;
    end

endmodule
