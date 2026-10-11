module TopModule (
    input  logic       clk,
    input  logic [7:0] in,
    output logic [7:0] pedge
);

    logic [7:0] prev;

    always_ff @(posedge clk) begin
        pedge <= in & ~prev;
        prev  <= in;
    end

endmodule
