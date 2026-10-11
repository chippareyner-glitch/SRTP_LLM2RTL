module TopModule (
  input  clk,
  input  resetn,
  input  [2:0] r,
  output [2:0] g
);

  localparam [1:0] A = 2'b00,
                   B = 2'b01,
                   C = 2'b10,
                   D = 2'b11;

  reg [1:0] state, next_state;

  // State table (combinational)
  always @(*) begin
    case (state)
      A: begin
        if      (r[0]) next_state = B;  // device 0 has highest priority
        else if (r[1]) next_state = C;  // device 1 next
        else if (r[2]) next_state = D;  // device 2 only if sole requester
        else           next_state = A;  // no requests: stay in A
      end
      B: next_state = r[0] ? B : A;     // hold grant while r[0] asserted
      C: next_state = r[1] ? C : A;     // hold grant while r[1] asserted
      D: next_state = r[2] ? D : A;     // hold grant while r[2] asserted
      default: next_state = A;
    endcase
  end

  // State flip-flops (synchronous active-low reset)
  always @(posedge clk) begin
    if (!resetn) state <= A;
    else         state <= next_state;
  end

  // Outputs
  assign g[0] = (state == B);
  assign g[1] = (state == C);
  assign g[2] = (state == D);

endmodule
