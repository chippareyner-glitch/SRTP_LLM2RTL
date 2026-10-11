module TopModule (
    input  logic       clk,
    input  logic       load,
    input  logic [9:0] data,
    output logic       tc
);

    logic [9:0] count;

    always_ff @(posedge clk) begin
        if (load)
            count <= data;
        else if (count != 0)
            count <= count - 1'b1;
    end

    assign tc = (count == 0);

endmodule
