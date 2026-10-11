module TopModule (
    input clk,
    input reset,
    output [3:1] ena,
    output [15:0] q
);

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 16'd0;
        end else begin
            q[3:0] <= (q[3:0] == 4'd9) ? 4'd0 : q[3:0] + 4'd1;
            if (q[3:0] == 4'd9)
                q[7:4] <= (q[7:4] == 4'd9) ? 4'd0 : q[7:4] + 4'd1;
            if (q[3:0] == 4'd9 && q[7:4] == 4'd9)
                q[11:8] <= (q[11:8] == 4'd9) ? 4'd0 : q[11:8] + 4'd1;
            if (q[3:0] == 4'd9 && q[7:4] == 4'd9 && q[11:8] == 4'd9)
                q[15:12] <= (q[15:12] == 4'd9) ? 4'd0 : q[15:12] + 4'd1;
        end
    end

    assign ena[1] = (q[3:0] == 4'd9);
    assign ena[2] = (q[3:0] == 4'd9) && (q[7:4] == 4'd9);
    assign ena[3] = (q[3:0] == 4'd9) && (q[7:4] == 4'd9) && (q[11:8] == 4'd9);

endmodule
