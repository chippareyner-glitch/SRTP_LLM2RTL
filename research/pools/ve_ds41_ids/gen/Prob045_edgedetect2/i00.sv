module TopModule (
    input clk,
    input [7:0] in,
    output logic [7:0] anyedge
);
    logic [7:0] prev;

    always_ff @(posedge clk) begin
        anyedge <= in ^ prev;
        prev <= in;
    end
endmodule
