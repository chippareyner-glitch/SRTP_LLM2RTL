module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [513:0] ext;
    logic [511:0] next_q;
    integer i;

    assign ext = {1'b0, q, 1'b0};

    always_comb begin
        for (i = 0; i < 512; i = i + 1) begin
            next_q[i] = (ext[i] & (ext[i+1] ^ ext[i+2])) |
                        (~ext[i] & (ext[i+1] | ext[i+2]));
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
