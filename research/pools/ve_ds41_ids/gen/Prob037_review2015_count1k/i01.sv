module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [9:0] q
);

    logic [9:0] count;

    always_ff @(posedge clk) begin
        if (reset) begin
            count <= 10'd0;
        end else begin
            if (count == 10'd999)
                count <= 10'd0;
            else
                count <= count + 10'd1;
        end
        q <= count;
    end

endmodule
