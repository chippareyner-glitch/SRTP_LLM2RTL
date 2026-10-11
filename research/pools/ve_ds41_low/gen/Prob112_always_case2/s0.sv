module TopModule (
    input  logic [3:0] in,
    output logic [1:0] pos
);

    always_comb begin
        casez (in)
            4'bzzz1: pos = 2'd0;
            4'bzz1z: pos = 2'd1;
            4'bz1zz: pos = 2'd2;
            4'b1zzz: pos = 2'd3;
            default: pos = 2'd0;
        endcase
    end

endmodule
