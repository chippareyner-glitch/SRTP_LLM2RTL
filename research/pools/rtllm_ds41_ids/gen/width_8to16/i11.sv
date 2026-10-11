module width_8to16 (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        valid_in,
    input  logic [7:0]  data_in,
    output logic        valid_out,
    output logic [15:0] data_out
);

    logic [7:0] data_lock;   // holds the first arriving byte
    logic       flag;        // indicates a pending byte is stored

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out  <= 16'h0000;
            valid_out <= 1'b0;
            data_lock <= 8'h00;
            flag      <= 1'b0;
        end
        else begin
            valid_out <= 1'b0;

            if (valid_in) begin
                if (flag) begin
                    // second consecutive valid byte: concatenate first (high) with second (low)
                    data_out  <= {data_lock, data_in};
                    valid_out <= 1'b1;
                    flag      <= 1'b0;
                end
                else begin
                    // first valid byte: store it, wait for the next one
                    data_lock <= data_in;
                    flag      <= 1'b1;
                end
            end
            else begin
                // pending byte is only valid for the immediately following cycle
                flag <= 1'b0;
            end
        end
    end

endmodule
