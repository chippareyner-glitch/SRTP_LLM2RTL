module TopModule (
    input  clk,
    input  resetn,          // active-low synchronous reset
    input  [2:0] r,         // requests from devices 0,1,2
    output [2:0] g          // grants  to   devices 0,1,2
);

    // State encoding
    localparam [1:0] A = 2'b00,
                     B = 2'b01,
                     C = 2'b10,
                     D = 2'b11;

    reg [1:0] state, next_state;

    // Next-state logic (state table)
    always @(*) begin
        case (state)
            A: begin
                if      (r[0]) next_state = B;  // device 0 highest priority
                else if (r[1]) next_state = C;  // device 1 next
                else if (r[2]) next_state = D;  // device 2 lowest
                else           next_state = A;
            end
            B: next_state = r[0] ? B : A;       // hold grant while r0
            C: next_state = r[1] ? C : A;       // hold grant while r1
            D: next_state = r[2] ? D : A;       // hold grant while r2
            default: next_state = A;
        endcase
    end

    // State flip-flops with synchronous active-low reset
    always @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next_state;
    end

    // Output logic (Moore): one-hot grants per state
    // B grants device 0 -> g[0]=1
    // C grants device 1 -> g[1]=1
    // D grants device 2 -> g[2]=1
    assign g = (state == B) ? 3'b001 :
               (state == C) ? 3'b010 :
               (state == D) ? 3'b100 :
                              3'b000;

endmodule
