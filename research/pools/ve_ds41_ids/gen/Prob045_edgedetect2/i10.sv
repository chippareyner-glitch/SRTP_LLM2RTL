module TopModule (
    input  logic       clk,
    input  logic [7:0] in,
    output logic [7:0] anyedge
);

    logic [7:0] prev = 8'b0;

    always_ff @(posedge clk) begin
        anyedge <= in ^ prev;
        prev    <= in;
    end

endmodule
