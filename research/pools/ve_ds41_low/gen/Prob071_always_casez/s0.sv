module TopModule (
    input  [7:0] in,
    output logic [2:0] pos
);

    always_comb begin
        pos = 3'd0;
        for (int i = 0; i < 8; i = i + 1) begin
            if (in[i]) begin
                pos = i[2:0];
                break;
            end
        end
    end

endmodule
