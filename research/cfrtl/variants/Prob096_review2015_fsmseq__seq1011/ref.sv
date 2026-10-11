module RefModule (
  input clk,
  input reset,
  input data,
  output start_shifting
);
  parameter S=0, S1=1, S10=2, S101=3, Done=4;
  reg [2:0] state, next;
  always_comb begin
    case (state)
      S:    next = data ? S1   : S;
      S1:   next = data ? S1   : S10;
      S10:  next = data ? S101 : S;
      S101: next = data ? Done : S10;
      Done: next = Done;
      default: next = S;
    endcase
  end
  always @(posedge clk)
    if (reset) state <= S;
    else       state <= next;
  assign start_shifting = state == Done;
endmodule
