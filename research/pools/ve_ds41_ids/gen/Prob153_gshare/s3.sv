module TopModule (
    input  clk,
    input  areset,
    input  predict_valid,
    input  [6:0] predict_pc,
    output logic predict_taken,
    output logic [6:0] predict_history,
    input  train_valid,
    input  train_taken,
    input  train_mispredicted,
    input  [6:0] train_history,
    input  [6:0] train_pc
);

    logic [1:0] pht [0:127];
    logic [6:0] ghr;

    wire [6:0] predict_index = predict_pc ^ ghr;
    wire [6:0] train_index   = train_pc ^ train_history;

    assign predict_taken   = pht[predict_index][1];
    assign predict_history = ghr;

    integer i;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            ghr <= 7'b0;
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b00;
            end
        end else begin
            // Update PHT for training
            if (train_valid) begin
                if (train_taken) begin
                    if (pht[train_index] != 2'b11)
                        pht[train_index] <= pht[train_index] + 1'b1;
                end else begin
                    if (pht[train_index] != 2'b00)
                        pht[train_index] <= pht[train_index] - 1'b1;
                end
            end

            // Update global history register
            if (train_valid && train_mispredicted) begin
                ghr <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                ghr <= {ghr[5:0], pht[predict_index][1]};
            end
        end
    end

endmodule
