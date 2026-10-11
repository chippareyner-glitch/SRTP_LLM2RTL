module accu (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data_in,
    input  wire        valid_in,
    output reg  [9:0]  data_out,
    output reg         valid_out
);

    reg [9:0] sum;
    reg [1:0] count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum       <= 10'd0;
            count     <= 2'd0;
            data_out  <= 10'd0;
            valid_out <= 1'b0;
        end
        else begin
            if (valid_in) begin
                if (count == 2'd3) begin
                    data_out  <= sum + data_in;
                    valid_out <= 1'b1;
                    sum       <= 10'd0;
                    count     <= 2'd0;
                end
                else begin
                    sum       <= sum + data_in;
                    count     <= count + 2'd1;
                    valid_out <= 1'b0;
                end
            end
            else begin
                sum       <= 10'd0;
                count     <= 2'd0;
                valid_out <= 1'b0;
            end
        end
    end

endmodule
