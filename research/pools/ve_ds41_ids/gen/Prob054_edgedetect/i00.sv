module TopModule (
    input  logic       clk,
    input  logic [7:0] in,
    output logic [7:0] pedge
);

    logic [7:0] prev;

    always_ff @(posedge clk) begin
        prev <= in;
    end

    assign pedge = in & ~prev;

endmodule
