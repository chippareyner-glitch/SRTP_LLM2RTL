module TopModule (
    input  logic clk,
    input  logic reset,
    output logic [3:1] ena,
    output logic [15:0] q
);

    logic [15:0] next_q;

    always_comb begin
        next_q = q;
        if (q[3:0] == 4'd9) begin
            next_q[3:0] = 4'd0;
            if (q[7:4] == 4'd9) begin
                next_q[7:4] = 4'd0;
                if (q[11:8] == 4'd9) begin
                    next_q[11:8] = 4'd0;
                    if (q[15:12] == 4'd9) begin
                        next_q[15:12] = 4'd0;
                    end else begin
                        next_q[15:12] = q[15:12] + 1'b1;
                    end
                end else begin
                    next_q[11:8] = q[11:8] + 1'b1;
                end
            end else begin
                next_q[7:4] = q[7:4] + 1'b1;
            end
        end else begin
            next_q[3:0] = q[3:0] + 1'b1;
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            q <= 16'h0000;
        end else begin
            q <= next_q;
        end
    end

    assign ena[1] = (q[7:4] == 4'd9);
    assign ena[2] = (q[11:8] == 4'd9);
    assign ena[3] = (q[15:12] == 4'd9);

endmodule
