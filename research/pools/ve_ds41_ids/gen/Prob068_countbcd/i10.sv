module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [2:0] ena,
    output logic [15:0] q
);

    always_comb begin
        ena[0] = (q[3:0] == 4'd9);
        ena[1] = (q[7:4] == 4'd9) && ena[0];
        ena[2] = (q[11:8] == 4'd9) && ena[1];
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 16'd0;
        end else begin
            if (q[3:0] == 4'd9)
                q[3:0] <= 4'd0;
            else
                q[3:0] <= q[3:0] + 4'd1;

            if (ena[0]) begin
                if (q[7:4] == 4'd9)
                    q[7:4] <= 4'd0;
                else
                    q[7:4] <= q[7:4] + 4'd1;
            end

            if (ena[1]) begin
                if (q[11:8] == 4'd9)
                    q[11:8] <= 4'd0;
                else
                    q[11:8] <= q[11:8] + 4'd1;
            end

            if (ena[2]) begin
                if (q[15:12] == 4'd9)
                    q[15:12] <= 4'd0;
                else
                    q[15:12] <= q[15:12] + 4'd1;
            end
        end
    end

endmodule
