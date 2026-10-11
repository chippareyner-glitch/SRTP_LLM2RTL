module TopModule (
    input  logic clk,
    input  logic [7:0] in,
    output logic [7:0] anyedge
);

    logic [7:0] prev;
    logic [7:0] edge_pulse;

    always_ff @(posedge clk) begin
        prev       <= in;
        edge_pulse <= in ^ prev;
        anyedge    <= edge_pulse;
    end

endmodule
