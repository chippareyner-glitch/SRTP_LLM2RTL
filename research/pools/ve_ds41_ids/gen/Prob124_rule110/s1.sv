module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    wire [511:0] next;
    wire [513:0] q_pad;

    assign q_pad = {1'b0, q, 1'b0};

    genvar i;
    generate
        for (i = 0; i < 512; i = i + 1) begin : gen_rule110
            assign next[i] = (~q_pad[i+2] & (q_pad[i+1] | q_pad[i])) |
                             (q_pad[i+2] & (q_pad[i+1] ^ q_pad[i]));
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            q <= next;
        end
    end

endmodule
