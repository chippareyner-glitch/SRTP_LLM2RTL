module TopModule (
    input  [254:0] in,
    output logic [7:0] out
);

    integer i;
    logic [7:0] pop_cnt;

    always_comb begin
        pop_cnt = 8'd0;
        for (i = 0; i < 255; i = i + 1) begin
            pop_cnt = pop_cnt + {7'b0, in[i]};
        end
    end

    assign out = pop_cnt;

endmodule
