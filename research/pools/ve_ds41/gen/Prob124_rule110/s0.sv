module TopModule(
    input  clk,
    input  load,
    input  [511:0] data,
    output logic [511:0] q
);

    logic [511:0] L, R, C, next;

    assign L = q >> 1;
    assign R = q << 1;
    assign C = q;
    assign next = (~L & C) | (~C & R) | (L & C & ~R);

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next;
    end

endmodule
