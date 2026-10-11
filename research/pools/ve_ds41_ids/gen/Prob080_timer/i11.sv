module TopModule (
    input clk,
    input load,
    input [9:0] data,
    output logic tc
);

    logic [9:0] counter;

    always_ff @(posedge clk) begin
        if (load) begin
            counter <= data;
        end else if (counter != 0) begin
            counter <= counter - 1;
        end else begin
            counter <= 0;
        end
        tc <= (counter == 0);
    end

endmodule
