module parallel2serial (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [3:0] d,
    output logic       valid_out,
    output wire        dout
);

    logic [3:0] data;
    logic [1:0] cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data      <= 4'b0000;
            cnt       <= 2'b00;
            valid_out <= 1'b0;
        end else begin
            if (cnt == 2'd3) begin
                data      <= d;
                cnt       <= 2'b00;
                valid_out <= 1'b1;
            end else begin
                cnt       <= cnt + 1'b1;
                valid_out <= 1'b0;
                data      <= {data[2:0], data[3]};
            end
        end
    end

    assign dout = data[3];

endmodule
