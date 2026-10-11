module ROM (
    input  wire [7:0]  addr,
    output reg  [15:0] dout
);

    // 256 x 16-bit ROM memory array
    reg [15:0] mem [0:255];

    integer i;

    // Pre-load ROM contents
    initial begin
        // Default all unspecified locations to zero
        for (i = 0; i < 256; i = i + 1) begin
            mem[i] = 16'h0000;
        end

        // Fixed predefined data
        mem[0] = 16'hA0A0;
        mem[1] = 16'hB1B1;
        mem[2] = 16'hC2C2;
        mem[3] = 16'hD3D3;
    end

    // Read-only access: continuously output data at address
    always @(*) begin
        dout = mem[addr];
    end

endmodule
