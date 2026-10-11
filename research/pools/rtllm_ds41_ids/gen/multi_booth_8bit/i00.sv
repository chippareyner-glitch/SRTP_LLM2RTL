module multi_booth_8bit (
    input  logic               clk,
    input  logic               reset,
    input  logic [7:0]         a,
    input  logic [7:0]         b,
    output logic signed [15:0] p,
    output logic               rdy
);

    logic signed [15:0] multiplier;
    logic signed [15:0] multiplicand;
    logic               Q_1;
    logic [4:0]         ctr;
    logic [2:0]         booth_code;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            multiplier   <= {{8{a[7]}}, a};
            multiplicand <= {{8{b[7]}}, b};
            p            <= 16'b0;
            Q_1          <= 1'b0;
            ctr          <= 5'd0;
            rdy          <= 1'b0;
        end else begin
            if (ctr < 5'd8) begin
                booth_code = {multiplier[1], multiplier[0], Q_1};
                case (booth_code)
                    3'b000, 3'b111: begin
                        // no operation (multiply by 0)
                    end
                    3'b001, 3'b010: begin
                        p <= p + multiplicand;
                    end
                    3'b011: begin
                        p <= p + (multiplicand << 1);
                    end
                    3'b100: begin
                        p <= p - (multiplicand << 1);
                    end
                    3'b101, 3'b110: begin
                        p <= p - multiplicand;
                    end
                endcase
                multiplicand <= multiplicand << 2;
                Q_1          <= multiplier[1];
                multiplier   <= multiplier >>> 2;
                ctr          <= ctr + 1;
            end else begin
                rdy <= 1'b1;
            end
        end
    end

endmodule
