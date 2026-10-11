module TopModule (
    input  clk,
    input  reset,
    output [2:0] ena,
    output [15:0] q
);

    reg [15:0] q_reg;

    assign q = q_reg;

    // Enable signals: each upper digit increments when all lower digits are 9
    assign ena[0] = (q_reg[3:0]  == 4'd9);
    assign ena[1] = ena[0] && (q_reg[7:4]  == 4'd9);
    assign ena[2] = ena[1] && (q_reg[11:8] == 4'd9);

    always @(posedge clk) begin
        if (reset) begin
            q_reg <= 16'd0;
        end else begin
            // Ones digit increments every clock
            if (q_reg[3:0] == 4'd9)
                q_reg[3:0] <= 4'd0;
            else
                q_reg[3:0] <= q_reg[3:0] + 4'd1;

            // Tens digit
            if (ena[0]) begin
                if (q_reg[7:4] == 4'd9)
                    q_reg[7:4] <= 4'd0;
                else
                    q_reg[7:4] <= q_reg[7:4] + 4'd1;
            end

            // Hundreds digit
            if (ena[1]) begin
                if (q_reg[11:8] == 4'd9)
                    q_reg[11:8] <= 4'd0;
                else
                    q_reg[11:8] <= q_reg[11:8] + 4'd1;
            end

            // Thousands digit
            if (ena[2]) begin
                if (q_reg[15:12] == 4'd9)
                    q_reg[15:12] <= 4'd0;
                else
                    q_reg[15:12] <= q_reg[15:12] + 4'd1;
            end
        end
    end

endmodule
