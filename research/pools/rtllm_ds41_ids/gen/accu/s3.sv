module accu (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    input  logic       valid_in,
    output logic       valid_out,
    output logic [9:0] data_out
);

    logic [9:0] acc;
    logic [1:0] cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc       <= 10'd0;
            cnt       <= 2'd0;
            data_out  <= 10'd0;
            valid_out <= 1'b0;
        end else begin
            valid_out <= 1'b0;

            if (valid_in) begin
                if (cnt == 2'd3) begin
                    data_out  <= acc + data_in;
                    valid_out <= 1'b1;
                    acc       <= 10'd0;
                    cnt       <= 2'd0;
                end else begin
                    acc <= acc + data_in;
                    cnt <= cnt + 2'd1;
                end
            end
        end
    end

endmodule
