module TopModule (
    input do_sub,
    input [7:0] a,
    input [7:0] b,
    output reg [7:0] out,
    output reg result_is_zero
);

    reg [8:0] full_result;

    always @(*) begin
        if (do_sub)
            full_result = {1'b0, a} - {1'b0, b};
        else
            full_result = {1'b0, a} + {1'b0, b};

        out = full_result[7:0];
        result_is_zero = (full_result == 9'd0);
    end

endmodule
