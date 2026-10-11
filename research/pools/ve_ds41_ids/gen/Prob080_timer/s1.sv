module TopModule (
    input  logic        clk,
    input  logic        load,
    input  logic [9:0]  data,
    output logic        tc
);

    logic [9:0] count;

    always_ff @(posedge clk) begin
        if (load) begin
            count <= data;
        end else if (count != 10'd0) begin
            count <= count - 10'd1;
        end else begin
            count <= count;
        end
    end

    assign tc = (count == 10'd0);

endmodule
