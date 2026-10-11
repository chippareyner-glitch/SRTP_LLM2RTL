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

    logic [6:0] bhr;
    logic [1:0] pht [0:127];

    wire [6:0] predict_index = predict_pc ^ bhr;
    wire [6:0] train_index = train_pc ^ train_history;

    assign predict_taken = pht[predict_index][1];
    assign predict_history = bhr;

    logic [6:0] bhr_next;
    always_comb begin
        if (train_valid && train_mispredicted)
            bhr_next = {train_history[5:0], train_taken};
        else if (predict_valid)
            bhr_next = {bhr[5:0], predict_taken};
        else
            bhr_next = bhr;
    end

    integer i;
    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            bhr <= 7'b0;
            for (i = 0; i < 128; i = i + 1)
                pht[i] <= 2'b00;
        end else begin
            bhr <= bhr_next;

            if (train_valid) begin
                if (train_taken) begin
                    if (pht[train_index] != 2'b11)
                        pht[train_index] <= pht[train_index] + 1'b1;
                end else begin
                    if (pht[train_index] != 2'b00)
                        pht[train_index] <= pht[train_index] - 1'b1;
                end
            end
        end
    end

endmodule
