module alu(
    input  [31:0] a,
    input  [31:0] b,
    input  [5:0]  aluc,
    output [31:0] r,
    output        zero,
    output        carry,
    output        negative,
    output        overflow,
    output reg    flag
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

    wire signed [31:0] signed_a = a;
    wire signed [31:0] signed_b = b;
    reg [32:0] res;

    assign r        = res[31:0];
    assign zero     = (r == 0);
    assign carry    = res[32];
    assign negative = res[31];
    assign overflow = (aluc == ADD) ? ((a[31] == b[31]) && (res[31] != a[31])) :
                      (aluc == SUB) ? ((a[31] != b[31]) && (res[31] != a[31])) : 1'b0;

    always @(*) begin
        flag = 1'bz;
        case (aluc)
            ADD:  res = {signed_a[31], signed_a} + {signed_b[31], signed_b};
            ADDU: res = {1'b0, a} + {1'b0, b};
            SUB:  res = {signed_a[31], signed_a} - {signed_b[31], signed_b};
            SUBU: res = {1'b0, a} - {1'b0, b};
            AND:  res = a & b;
            OR:   res = a | b;
            XOR:  res = a ^ b;
            NOR:  res = ~(a | b);
            SLT:  begin
                res = (signed_a < signed_b) ? 1 : 0;
                flag = 1'b1;
            end
            SLTU: begin
                res = (a < b) ? 1 : 0;
                flag = 1'b1;
            end
            SLL:  res = b << a[4:0];
            SRL:  res = b >> a[4:0];
            SRA:  res = signed_b >>> a[4:0];
            SLLV: res = b << a[4:0];
            SRLV: res = b >> a[4:0];
            SRAV: res = signed_b >>> a[4:0];
            LUI:  res = {a[15:0], 16'b0};
            default: res = 32'bz;
        endcase
    end

endmodule
