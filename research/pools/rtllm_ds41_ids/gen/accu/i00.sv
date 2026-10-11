module accu (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [7:0]  data_in,
    input  logic        valid_in,
    output logic        valid_out,
    output logic [9:0]  data_out
);

    logic [1:0] cnt;   // number of samples already accumulated (0..3)
    logic [9:0] acc;   // running partial accumulation

    wire  [9:0] sum_next = acc + {2'b00, data_in};
    wire        last     = valid_in && (cnt == 2'd3);

    // Combinational outputs, valid in the same cycle the 4th sample is accepted
    assign valid_out = last;
    assign data_out  = sum_next;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 2'd0;
            acc <= 10'd0;
        end else if (valid_in) begin
            if (cnt == 2'd3) begin
                cnt <= 2'd0;      // group complete, restart accumulation
                acc <= 10'd0;
            end else begin
                cnt <= cnt + 2'd1;
                acc <= sum_next;  // store partial sum of 1..3 samples
            end
        end
    end

endmodule
