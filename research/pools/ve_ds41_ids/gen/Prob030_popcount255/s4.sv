module TopModule (
    input  logic [254:0] in,
    output logic [7:0]   out
);

    always_comb begin
        out = 8'd0;
        for (int i = 0; i < 255; i++) begin
            out += in[i];
        end
    end

endmodule
