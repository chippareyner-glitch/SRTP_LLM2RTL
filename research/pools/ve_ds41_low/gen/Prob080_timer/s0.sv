module TopModule (
    input  clk,
    input  load,
    input  [9:0] data,
    output logic tc
);

    logic [9:0] counter;

    always_ff @(posedge clk) begin
        if (load)
            counter <= data;
        else if (counter != 10'd0)
            counter <= counter - 10'd1;
    end

    assign tc = (counter == 10'd0);

endmodule
