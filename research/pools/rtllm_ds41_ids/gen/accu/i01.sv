module accu (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [7:0]  data_in,
    input  logic        valid_in,
    output logic        valid_out,
    output logic [9:0]  data_out
);

    logic [1:0] cnt;
    logic [9:0] sum;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt       <= 2'd0;
            sum       <= 10'd0;
            data_out  <= 10'd0;
            valid_out <= 1'b0;
        end else begin
            valid_out <= 1'b0;
            if (valid_in) begin
                if (cnt == 2'd3) begin
                    data_out  <= sum + data_in;
                    valid_out <= 1'b1;
                    sum       <= 10'd0;
                    cnt       <= 2'd0;
                end else begin
                    sum <= sum + data_in;
                    cnt <= cnt + 2'd1;
                end
            end
        end
    end

endmodule
