module TopModule (
    input  logic        clk,
    input  logic        areset,
    input  logic        predict_valid,
    input  logic [6:0]  predict_pc,
    output logic        predict_taken,
    output logic [6:0]  predict_history,
    input  logic        train_valid,
    input  logic        train_taken,
    input  logic        train_mispredicted,
    input  logic [6:0]  train_history,
    input  logic [6:0]  train_pc
);

    logic [6:0] history;
    logic [1:0] pht [0:127];
    logic [6:0] predict_index;
    logic [6:0] train_index;
    integer i;

    assign predict_index = predict_pc ^ history;
    assign train_index = train_pc ^ train_history;

    assign predict_history = history;
    assign predict_taken = pht[predict_index][1];

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            history <= 7'b0;
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b00;
            end
        end else begin
            if (train_valid) begin
                if (train_taken) begin
                    if (pht[train_index] != 2'b11)
                        pht[train_index] <= pht[train_index] + 1'b1;
                end else begin
                    if (pht[train_index] != 2'b00)
                        pht[train_index] <= pht[train_index] - 1'b1;
                end
            end

            if (train_valid && train_mispredicted) begin
                history <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                history <= {history[5:0], predict_taken};
            end
        end
    end

endmodule
