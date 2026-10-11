module TopModule(
  input  clk,
  input  resetn,
  input  [2:0] r,
  output [2:0] g
);

  localparam A = 2'b00,
             B = 2'b01,
             C = 2'b10,
             D = 2'b11;

  reg [1:0] state, nextstate;

  // State table (combinational next-state logic)
  always @(*) begin
    case (state)
      A: begin
        if      (r[0]) nextstate = B;
        else if (r[1]) nextstate = C;
        else if (r[2]) nextstate = D;
        else           nextstate = A;
      end
      B: nextstate = r[0] ? B : A;
      C: nextstate = r[1] ? C : A;
      D: nextstate = r[2] ? D : A;
      default: nextstate = A;
    endcase
  end

  // State flip-flops with active-low synchronous reset
  always @(posedge clk) begin
    if (!resetn)
      state <= A;
    else
      state <= nextstate;
  end

  // Output logic: B grants device 0, C grants device 1, D has no grant
  assign g = (state == B) ? 3'b001 :
             (state == C) ? 3'b010 :
                            3'b000;

endmodule
