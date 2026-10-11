module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [4:0] q
);

    always_ff @(posedge clk) begin
        if (reset)
            q <= 5'b00001;
        else
            q <= (q >> 1) ^ ({5{q[0]}} & 5'b10100);
    end

endmodule
