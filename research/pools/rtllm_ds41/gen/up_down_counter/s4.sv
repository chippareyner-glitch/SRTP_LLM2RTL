module up_down_counter (
    input  logic        clk,
    input  logic        reset,
    input  logic        up_down,
    output logic [15:0] count
);

    always_ff @(posedge clk) begin
        if (reset)
            count <= 16'd0;
        else if (up_down)
            count <= count + 16'd1;
        else
            count <= count - 16'd1;
    end

endmodule
