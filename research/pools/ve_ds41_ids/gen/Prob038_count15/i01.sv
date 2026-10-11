module TopModule (
    input  logic       clk,
    input  logic       reset,
    output logic [3:0] q
);

    logic [3:0] cnt;

    always_ff @(posedge clk) begin
        if (reset)
            cnt <= 4'd0;
        else
            cnt <= cnt + 4'd1;
    end

    // q[0] is MSB, q[3] is LSB (reversed bit order)
    assign q = {cnt[0], cnt[1], cnt[2], cnt[3]};

endmodule
