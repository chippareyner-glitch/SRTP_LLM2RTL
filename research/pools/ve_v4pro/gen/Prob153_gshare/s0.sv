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

    logic [6:0] ghr;
    logic [1:0] pht [0:127];

    wire [6:0] predict_index = predict_pc ^ ghr;
    wire [6:0] train_index   = train_pc ^ train_history;
    wire [1:0] predict_entry = pht[predict_index];

    assign predict_taken   = predict_entry[1];
    assign predict_history = ghr;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            ghr <= 7'h0;
        end else begin
            if (train_valid && train_mispredicted) begin
                ghr <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                ghr <= {ghr[5:0], predict_taken};
            end
        end
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            for (int i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b00;
            end
        end else if (train_valid) begin
            if (train_taken) begin
                if (pht[train_index] != 2'b11)
                    pht[train_index] <= pht[train_index] + 2'b01;
            end else begin
                if (pht[train_index] != 2'b00)
                    pht[train_index] <= pht[train_index] - 2'b01;
            end
        end
    end

endmodule
