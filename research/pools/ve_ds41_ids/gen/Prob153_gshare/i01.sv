module TopModule (
    input  wire        clk,
    input  wire        areset,

    input  wire        predict_valid,
    input  wire [6:0]  predict_pc,
    output wire        predict_taken,
    output wire [6:0]  predict_history,

    input  wire        train_valid,
    input  wire        train_taken,
    input  wire        train_mispredicted,
    input  wire [6:0]  train_history,
    input  wire [6:0]  train_pc
);

    // 128-entry pattern history table of 2-bit saturating counters.
    // Counter encoding: 0 = strongly taken, 3 = strongly not-taken.
    reg [1:0] pht [0:127];
    reg [6:0] history;

    wire [6:0] predict_index = predict_pc ^ history;
    wire [6:0] train_index   = train_pc   ^ train_history;

    // prediction sees the PHT state before any same-cycle training update
    assign predict_taken   = ~pht[predict_index][1]; // inverted MSB
    assign predict_history = history;

    integer i;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            history <= 7'b0;
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b00; // strongly taken
            end
        end else begin
            // Branch history register update.
            // Misprediction training takes precedence over prediction.
            if (train_valid && train_mispredicted) begin
                history <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                history <= {history[5:0], predict_taken};
            end

            // PHT update: train_taken=1 decrements, train_taken=0 increments.
            if (train_valid) begin
                if (train_taken) begin
                    if (pht[train_index] != 2'b00)
                        pht[train_index] <= pht[train_index] - 1'b1;
                end else begin
                    if (pht[train_index] != 2'b11)
                        pht[train_index] <= pht[train_index] + 1'b1;
                end
            end
        end
    end

endmodule
