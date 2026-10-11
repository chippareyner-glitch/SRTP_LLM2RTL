module parallel2serial (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [3:0] d,
    output logic       valid_out,
    output logic       dout
);

    logic [3:0] data;
    logic [1:0] cnt;
    logic       valid;

    assign dout      = data[3];
    assign valid_out = valid;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt   <= 2'd0;
            data  <= 4'd0;
            valid <= 1'b0;
        end else begin
            if (cnt == 2'd3) begin
                data  <= d;
                cnt   <= 2'd0;
                valid <= 1'b1;
            end else begin
                cnt   <= cnt + 2'd1;
                valid <= 1'b0;
                data  <= {data[2:0], data[3]};
            end
        end
    end

endmodule
