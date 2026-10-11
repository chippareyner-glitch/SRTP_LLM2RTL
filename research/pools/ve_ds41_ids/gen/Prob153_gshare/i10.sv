module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic predict_valid,
  input  logic [6:0] predict_pc,
  output logic predict_taken,
  output logic [6:0] predict_history,
  input  logic train_valid,
  input  logic train_taken,
  input  logic train_mispredicted,
  input  logic [6:0] train_history,
  input  logic [6:0] train_pc
);

  logic [1:0] pht [0:127];
  logic [6:0] bhr;
  logic [6:0] predict_index;
  logic [6:0] train_index;
  integer i;

  assign predict_index = predict_pc ^ bhr;
  assign train_index   = train_pc ^ train_history;

  assign predict_taken   = pht[predict_index][1];
  assign predict_history = bhr;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      bhr <= 7'b0;
      for (i = 0; i < 128; i = i + 1) begin
        pht[i] <= 2'b01;
      end
    end else begin
      if (train_valid) begin
        case (pht[train_index])
          2'b00: pht[train_index] <= train_taken ? 2'b01 : 2'b00;
          2'b01: pht[train_index] <= train_taken ? 2'b10 : 2'b00;
          2'b10: pht[train_index] <= train_taken ? 2'b11 : 2'b01;
          2'b11: pht[train_index] <= train_taken ? 2'b11 : 2'b10;
        endcase
      end

      if (train_valid && train_mispredicted) begin
        bhr <= {train_history[5:0], train_taken};
      end else if (predict_valid) begin
        bhr <= {bhr[5:0], predict_taken};
      end
    end
  end

endmodule
