module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [511:0] next_q;
    logic [511:0] load_next_q;

    always_comb begin
        for (int i = 0; i < 512; i++) begin
            if (i == 0) begin
                next_q[i]      = q[1];
                load_next_q[i] = data[1];
            end
            else if (i == 511) begin
                next_q[i]      = q[510];
                load_next_q[i] = data[510];
            end
            else begin
                next_q[i]      = q[i-1] ^ q[i+1];
                load_next_q[i] = data[i-1] ^ data[i+1];
            end
        end
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= load_next_q;
        else
            q <= next_q;
    end

endmodule
