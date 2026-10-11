module div_16bit (
    input  logic [15:0] A,
    input  logic [7:0]  B,
    output logic [15:0] result,
    output logic [15:0] odd
);

    logic [15:0] a_reg;
    logic [7:0]  b_reg;

    // First always block: register inputs
    always_comb begin
        a_reg = A;
        b_reg = B;
    end

    // Second always block: restoring division
    always_comb begin
        logic [8:0]  rem;
        logic [15:0] quo;
        integer i;

        rem = 9'b0;
        quo = 16'b0;

        for (i = 15; i >= 0; i = i - 1) begin
            rem = {rem[7:0], A[i]};
            if (rem >= {1'b0, B}) begin
                rem = rem - {1'b0, B};
                quo[i] = 1'b1;
            end else begin
                quo[i] = 1'b0;
            end
        end

        result = quo;
        odd    = {7'b0, rem};
    end

endmodule
