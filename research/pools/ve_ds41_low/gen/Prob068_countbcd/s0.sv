module TopModule (
    input  logic        clk,
    input  logic        reset,
    output logic [2:0]  ena,
    output logic [15:0] q
);

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 16'd0;
        end else begin
            if (q[3:0] == 4'd9) begin
                q[3:0] <= 4'd0;
                if (q[7:4] == 4'd9) begin
                    q[7:4] <= 4'd0;
                    if (q[11:8] == 4'd9) begin
                        q[11:8] <= 4'd0;
                        if (q[15:12] == 4'd9)
                            q[15:12] <= 4'd0;
                        else
                            q[15:12] <= q[15:12] + 4'd1;
                    end else begin
                        q[11:8] <= q[11:8] + 4'd1;
                    end
                end else begin
                    q[7:4] <= q[7:4] + 4'd1;
                end
            end else begin
                q[3:0] <= q[3:0] + 4'd1;
            end
        end
    end

    assign ena[0] = (q[3:0]  == 4'd9);
    assign ena[1] = ena[0] && (q[7:4]  == 4'd9);
    assign ena[2] = ena[1] && (q[11:8] == 4'd9);

endmodule
