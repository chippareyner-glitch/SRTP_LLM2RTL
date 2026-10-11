module up_down_counter (
    input  logic        clk,
    input  logic        reset,
    input  logic        up_down,
    output logic [15:0] count
);

    always_ff @(posedge clk) begin
        if (reset) begin
            count <= 16'd0;
        end
        else if (up_down) begin
            count <= count + 16'd1;  // wraps 65535 -> 0
        end
        else begin
            count <= count - 16'd1;  // wraps 0 -> 65535
        end
    end

endmodule
