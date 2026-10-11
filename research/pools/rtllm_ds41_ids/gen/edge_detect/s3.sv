module edge_detect (
    input  logic clk,
    input  logic rst_n,
    input  logic a,
    output logic rise,
    output logic down
);

    logic a_d;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_d  <= 1'b0;
            rise <= 1'b0;
            down <= 1'b0;
        end else begin
            a_d  <= a;
            rise <= a  & ~a_d;
            down <= ~a &  a_d;
        end
    end

endmodule
