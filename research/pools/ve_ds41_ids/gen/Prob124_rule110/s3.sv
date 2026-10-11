module TopModule (
    input  logic clk,
    input  logic load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [511:0] q_next;

    assign q_next = ((q << 1) & ~(q >> 1)) | (q ^ (q << 1));

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= q_next;
    end

endmodule
