module TopModule (
    input  logic       clk,
    input  logic       load,
    input  logic [9:0] data,
    output logic       tc
);

    logic [9:0] counter;

    always_ff @(posedge clk) begin
        if (load) begin
            counter <= data;
        end else if (counter != 10'd0) begin
            counter <= counter - 10'd1;
        end
    end

    assign tc = (counter == 10'd0);

endmodule
