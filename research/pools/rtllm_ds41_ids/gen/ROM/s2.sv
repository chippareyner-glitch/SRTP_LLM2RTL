module ROM (
    input  logic [7:0]  addr,
    output logic [15:0] dout
);

    // 256 x 16-bit read-only memory array
    logic [15:0] mem [0:255];

    // Pre-load fixed ROM contents
    initial begin
        mem[0] = 16'hA0A0;
        mem[1] = 16'hB1B1;
        mem[2] = 16'hC2C2;
        mem[3] = 16'hD3D3;
        // Remaining locations default to 16'h0000
    end

    // Continuous read of the addressed location
    always_comb begin
        dout = mem[addr];
    end

endmodule
