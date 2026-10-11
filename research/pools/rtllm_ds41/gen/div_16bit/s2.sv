module div_16bit (
    input  logic [15:0] A,
    input  logic [7:0]  B,
    output logic [15:0] result,
    output logic [15:0] odd
);

    logic [15:0] a_reg;
    logic [7:0]  b_reg;

    always_comb begin
        a_reg = A;
        b_reg = B;
    end

    always_comb begin
        logic [15:0] q;
        logic [7:0]  r;
        logic [8:0]  temp;
        q = 16'b0;
        r = 8'b0;
        if (b_reg == 8'b0) begin
            q = 16'hFFFF;
            r = 8'hFF;
        end else begin
            for (int i = 15; i >= 0; i = i - 1) begin
                temp = {r, a_reg[i]};
                if (temp >= {1'b0, b_reg}) begin
                    q[i] = 1'b1;
                    r = temp[7:0] - b_reg;
                end else begin
                    q[i] = 1'b0;
                    r = temp[7:0];
                end
            end
        end
        result = q;
        odd = {8'b0, r};
    end

endmodule
