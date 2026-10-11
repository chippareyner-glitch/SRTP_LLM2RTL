module width_8to16 (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        valid_in,
    input  logic [7:0]  data_in,
    output logic        valid_out,
    output logic [15:0] data_out
);

    logic       flag;
    logic [7:0] data_lock;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            flag      <= 1'b0;
            data_lock <= 8'h00;
            valid_out <= 1'b0;
            data_out  <= 16'h0000;
        end else begin
            valid_out <= 1'b0;

            if (valid_in) begin
                if (flag) begin
                    data_out  <= {data_lock, data_in};
                    valid_out <= 1'b1;
                    flag      <= 1'b0;
                end else begin
                    data_lock <= data_in;
                    flag      <= 1'b1;
                end
            end
        end
    end

endmodule
