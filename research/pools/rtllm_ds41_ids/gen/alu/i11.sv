module alu
(
    input  wire        clk,       // implicit clock: res is a real register
    input  wire [31:0] a,         // first operand
    input  wire [31:0] b,         // second operand
    input  wire [5:0]  aluc,      // operation select
    output wire [31:0] r,         // result (registered -> 1 cycle latency)
    output wire        zero,      // result == 0
    output wire        carry,     // carry out of bit 31 (add / sub)
    output wire        negative,  // sign bit of the result
    output wire        overflow,  // signed overflow
    output wire        flag       // SLT / SLTU result flag
);

    parameter ADD  = 6'b100000;
    parameter ADDU = 6'b100001;
    parameter SUB  = 6'b100010;
    parameter SUBU = 6'b100011;
    parameter AND  = 6'b100100;
    parameter OR   = 6'b100101;
    parameter XOR  = 6'b100110;
    parameter NOR  = 6'b100111;
    parameter SLT  = 6'b101010;
    parameter SLTU = 6'b101011;
    parameter SLL  = 6'b000000;
    parameter SRL  = 6'b000010;
    parameter SRA  = 6'b000011;
    parameter SLLV = 6'b000100;
    parameter SRLV = 6'b000110;
    parameter SRAV = 6'b000111;
    parameter LUI  = 6'b001111;

    // 33-bit register: res[31:0] = result, res[32] = carry out
    reg [32:0] res;

    always @(posedge clk) begin
        case (aluc)
            ADD, ADDU : res = {1'b0, a} + {1'b0, b};
            SUB, SUBU : res = {1'b0, a} + {1'b0, ~b} + 33'b1;
            AND       : res = {1'b0, a & b};
            OR        : res = {1'b0, a | b};
            XOR       : res = {1'b0, a ^ b};
            NOR       : res = {1'b0, ~(a | b)};
            SLT       : res = {32'b0, ($signed(a) < $signed(b)) ? 1'b1 : 1'b0};
            SLTU      : res = {32'b0, (a < b) ? 1'b1 : 1'b0};
            SLL, SLLV : res = {1'b0, b << a[4:0]};
            SRL, SRLV : res = {1'b0, b >> a[4:0]};
            SRA, SRAV : res = {1'b0, ($signed(b) >>> a[4:0])};
            LUI       : res = {1'b0, a[15:0], 16'b0};
            default   : res = 33'bz;
        endcase
    end

    // signed overflow detection (operands/results are the same for ADD/ADDU, SUB/SUBU)
    wire add_ovf = (~a[31] & ~b[31] &  res[31]) |
                   ( a[31] &  b[31] & ~res[31]);

    wire sub_ovf = (~a[31] &  b[31] &  res[31]) |
                   ( a[31] & ~b[31] & ~res[31]);

    assign r         = res[31:0];

    assign zero      = (res[31:0] == 32'b0);

    assign negative  = res[31];

    assign carry     = ((aluc == ADD)  || (aluc == ADDU) ||
                        (aluc == SUB)  || (aluc == SUBU)) ? res[32] : 1'b0;

    assign overflow  = ((aluc == ADD)  || (aluc == ADDU)) ? add_ovf :
                       ((aluc == SUB)  || (aluc == SUBU)) ? sub_ovf : 1'b0;

    assign flag      = ((aluc == SLT)  || (aluc == SLTU)) ? 1'b1 : 1'bz;

endmodule
