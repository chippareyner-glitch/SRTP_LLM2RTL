module TopModule (
    input clk,
    input [7:0] in,
    output [7:0] anyedge
);
    logic [7:0] prev;
    always_ff @(posedge clk) begin
        prev <= in;
    end
    assign anyedge = in ^ prev;
endmodule
