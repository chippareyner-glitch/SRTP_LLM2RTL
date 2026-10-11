module multi_booth_8bit (
    input  wire        clk,
    input  wire        reset,
    input  wire [7:0]  a,
    input  wire [7:0]  b,
    output reg  [15:0] p,
    output reg         rdy
);

    reg [15:0] multiplier;    // holds sign-extended multiplicand input 'a'
    reg [15:0] multiplicand;  // holds sign-extended multiplier input 'b'
    reg [4:0]  ctr;           // 5-bit iteration counter

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            // Asynchronous reset: load registers, clear product and control
            multiplier   <= {{8{a[7]}}, a};
            multiplicand <= {{8{b[7]}}, b};
            p            <= 16'd0;
            ctr          <= 5'd0;
            rdy          <= 1'b0;
        end
        else begin
            if (ctr < 5'd16) begin
                // Shift the multiplicand left by one for the next bit position
                multiplicand <= multiplicand << 1;

                // If the current multiplier bit is 1, accumulate the multiplicand
                if (multiplier[ctr[3:0]])
                    p <= p + multiplicand;

                ctr <= ctr + 5'd1;
            end
            else begin
                // All 16 cycles completed: multiplication finished
                rdy <= 1'b1;
            end
        end
    end

endmodule
