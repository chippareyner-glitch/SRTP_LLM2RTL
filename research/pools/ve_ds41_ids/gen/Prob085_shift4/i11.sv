module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       load,
    input  wire       ena,
    input  wire [3:0] data,
    output logic [3:0] q
);

    always_ff @(posedge clk or negedge areset) begin
        if (!areset) begin
            q <= 4'b0000;
        end else if (load) begin
            q <= data;
        end else if (ena) begin
            q <= {1'b0, q[3:1]};
        end
    end

endmodule
