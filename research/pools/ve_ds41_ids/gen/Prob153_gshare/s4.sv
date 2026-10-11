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

    logic [6:0] history_reg;
    logic [1:0] pht [0:127];

    logic [6:0] predict_index;
    logic [6:0] train_index;

    assign predict_index = predict_pc ^ history_reg;
    assign train_index = train_pc ^ train_history;

    assign predict_taken = pht[predict_index][1];
    assign predict_history = history_reg;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            history_reg <= 7'b0;
            for (int i = 0; i < 128; i++) begin
                pht[i] <= 2'b01;
            end
        end else begin
            // PHT update
            if (train_valid) begin
                if (train_taken) begin
                    if (pht[train_index] != 2'b11)
                        pht[train_index] <= pht[train_index] + 1'b1;
                end else begin
                    if (pht[train_index] != 2'b00)
                        pht[train_index] <= pht[train_index] - 1'b1;
                end
            end

            // History register update
            if (train_valid && train_mispredicted) begin
                history_reg <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                history_reg <= {history_reg[5:0], predict_taken};
            end
        end
    end

endmodule
