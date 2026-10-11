module ROM (
    input  wire [7:0]  addr,
    output reg  [15:0] dout
);

    // 256 x 16-bit ROM array
    reg [15:0] mem [0:255];

    integer i;

    // Initial block: pre-loads the ROM with fixed data.
    // NOTE: The initial block is simulation-only and is ignored by synthesis,
    //       so the ROM contents are NOT guaranteed in hardware.
    initial begin
        for (i = 0; i < 256; i = i + 1) begin
            mem[i] = 16'h0000;          // other locations initialized as needed
        end
        mem[0] = 16'hA0A0;
        mem[1] = 16'hB1B1;
        mem[2] = 16'hC2C2;
        mem[3] = 16'hD3D3;
    end

    // Read-only access: continuously drive dout with the addressed location
    always @(*) begin
        dout = mem[addr];
    end

endmodule
