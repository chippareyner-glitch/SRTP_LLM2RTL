module ROM (
    input  wire [7:0]  addr,
    output reg  [15:0] dout
);

    // ROM: 256 locations x 16 bits
    reg [15:0] mem [0:255];

    // Pre-load fixed data. Only addresses 0-3 are specified;
    // addresses 4-255 remain uninitialized (X in simulation).
    initial begin
        mem[0] = 16'hA0A0;
        mem[1] = 16'hB1B1;
        mem[2] = 16'hC2C2;
        mem[3] = 16'hD3D3;
    end

    // Read-only, purely combinational access
    always @(*) begin
        dout = mem[addr];
    end

endmodule
