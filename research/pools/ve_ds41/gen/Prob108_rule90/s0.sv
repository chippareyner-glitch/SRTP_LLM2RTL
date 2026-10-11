module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output logic [511:0] q
);

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= (q << 1) ^ (q >> 1);
    end

endmodule
