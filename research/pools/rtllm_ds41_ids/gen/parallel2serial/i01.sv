module parallel2serial (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [3:0] d,
    output logic       valid_out,
    output wire        dout
);

    logic [3:0] data;
    logic [1:0] cnt;

    assign dout = data[3];

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cnt <= 2'b00;
        end else begin
            cnt <= cnt + 1'b1;
            if (cnt == 2'd3) begin
                data <= d;
                valid_out <= 1'b1;
            end else begin
                data <= {data[2:0], data[3]};
                valid_out <= 1'b0;
            end
        end
    end

endmodule
