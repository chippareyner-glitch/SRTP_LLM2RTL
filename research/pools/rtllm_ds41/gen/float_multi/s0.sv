module float_multi (
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg  [31:0] z
);

    reg [2:0]  counter;
    reg [23:0] a_mantissa, b_mantissa, z_mantissa;
    reg [9:0]  a_exponent, b_exponent, z_exponent;
    reg        a_sign, b_sign, z_sign;
    reg [49:0] product;
    reg        guard_bit, round_bit, sticky;

    reg        a_nan, b_nan, a_inf, b_inf, a_zero, b_zero;

    // Temporary variables for rounding stage
    reg [24:0] rounded_sum;
    reg [23:0] final_mant;
    reg [9:0]  final_exp;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter     <= 3'd0;
            z           <= 32'd0;
            a_mantissa  <= 24'd0;
            b_mantissa  <= 24'd0;
            z_mantissa  <= 24'd0;
            a_exponent  <= 10'd0;
            b_exponent  <= 10'd0;
            z_exponent  <= 10'd0;
            a_sign      <= 1'b0;
            b_sign      <= 1'b0;
            z_sign      <= 1'b0;
            product     <= 50'd0;
            guard_bit   <= 1'b0;
            round_bit   <= 1'b0;
            sticky      <= 1'b0;
            a_nan       <= 1'b0;
            b_nan       <= 1'b0;
            a_inf       <= 1'b0;
            b_inf       <= 1'b0;
            a_zero      <= 1'b0;
            b_zero      <= 1'b0;
        end else begin
            case (counter)
                3'd0: begin
                    // Input processing
                    a_sign      <= a[31];
                    b_sign      <= b[31];
                    a_exponent  <= {2'b0, a[30:23]};
                    b_exponent  <= {2'b0, b[30:23]};
                    a_mantissa  <= (a[30:23] == 8'h00) ? {1'b0, a[22:0]} : {1'b1, a[22:0]};
                    b_mantissa  <= (b[30:23] == 8'h00) ? {1'b0, b[22:0]} : {1'b1, b[22:0]};
                    a_nan       <= (a[30:23] == 8'hFF) && (a[22:0] != 0);
                    b_nan       <= (b[30:23] == 8'hFF) && (b[22:0] != 0);
                    a_inf       <= (a[30:23] == 8'hFF) && (a[22:0] == 0);
                    b_inf       <= (b[30:23] == 8'hFF) && (b[22:0] == 0);
                    a_zero      <= (a[30:23] == 8'h00) && (a[22:0] == 0);
                    b_zero      <= (b[30:23] == 8'h00) && (b[22:0] == 0);
                    counter     <= 3'd1;
                end

                3'd1: begin
                    product <= a_mantissa * b_mantissa;
                    counter <= 3'd2;
                end

                3'd2: begin
                    // Normalization and extraction of guard/round/sticky
                    if (product[47]) begin
                        z_exponent <= a_exponent + b_exponent - 127 + 1;
                        z_mantissa <= product[47:24];
                        guard_bit  <= product[23];
                        round_bit  <= product[22];
                        sticky     <= |product[21:0];
                    end else begin
                        z_exponent <= a_exponent + b_exponent - 127;
                        z_mantissa <= product[46:23];
                        guard_bit  <= product[22];
                        round_bit  <= product[21];
                        sticky     <= |product[20:0];
                    end
                    counter <= 3'd3;
                end

                3'd3: begin
                    // Rounding and output generation
                    z_sign <= a_sign ^ b_sign;

                    if (a_nan || b_nan || (a_inf && b_zero) || (b_inf && a_zero)) begin
                        z <= 32'h7FC00000; // NaN
                    end else if (a_inf || b_inf) begin
                        z <= {a_sign ^ b_sign, 8'hFF, 23'h0}; // Infinity
                    end else if (a_zero || b_zero) begin
                        z <= {a_sign ^ b_sign, 31'h0}; // Zero
                    end else begin
                        // Normal computation
                        final_mant = z_mantissa;
                        final_exp  = z_exponent;

                        if (guard_bit && (round_bit || sticky || z_mantissa[0])) begin
                            rounded_sum = {1'b0, z_mantissa} + 1;
                            if (rounded_sum[24]) begin
                                final_mant = 24'h800000;
                                final_exp  = z_exponent + 1;
                            end else begin
                                final_mant = rounded_sum[23:0];
                            end
                        end

                        if (final_exp >= 255) begin
                            z <= {z_sign, 8'hFF, 23'h0}; // Infinity (overflow)
                        end else if (final_exp < 1) begin
                            z <= {z_sign, 31'h0}; // Zero (underflow)
                        end else begin
                            z <= {z_sign, final_exp[7:0], final_mant[22:0]};
                        end

                        z_mantissa <= final_mant;
                        z_exponent <= final_exp;
                    end
                    counter <= 3'd4;
                end

                3'd4: begin
                    counter <= 3'd0;
                end

                default: counter <= 3'd0;
            endcase
        end
    end

endmodule
