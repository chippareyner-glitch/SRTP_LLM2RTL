module alu(
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [5:0]  aluc,
    output logic [31:0] r,
    output logic        zero,
    output logic        carry,
    output logic        negative,
    output logic        overflow,
    output logic        flag
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

    wire signed [31:0] sa = a;
    wire signed [31:0] sb = b;
    logic [31:0] res;
    logic        carry_out;
    logic        overflow_out;

    always @(*) begin
        carry_out    = 1'b0;
        overflow_out = 1'b0;
        res          = 32'b0;

        case (aluc)
            ADD: begin
                {carry_out, res} = a + b;
                overflow_out = (a[31] == b[31]) && (res[31] != a[31]);
            end
            ADDU: begin
                {carry_out, res} = a + b;
            end
            SUB: begin
                {carry_out, res} = a - b;
                overflow_out = (a[31] != b[31]) && (res[31] != a[31]);
            end
            SUBU: begin
                {carry_out, res} = a - b;
            end
            AND:  res = a & b;
            OR:   res = a | b;
            XOR:  res = a ^ b;
            NOR:  res = ~(a | b);
            SLT:  res = (sa < sb) ? 32'd1 : 32'd0;
            SLTU: res = (a < b) ? 32'd1 : 32'd0;
            SLL:  res = b << a[4:0];
            SRL:  res = b >> a[4:0];
            SRA:  res = sb >>> a[4:0];
            SLLV: res = b << a[4:0];
            SRLV: res = b >> a[4:0];
            SRAV: res = sb >>> a[4:0];
            LUI:  res = {a[15:0], 16'b0};
            default: res = 32'b0;
        endcase
    end

    assign r        = res;
    assign zero     = (res == 32'b0);
    assign negative = res[31];
    assign carry    = carry_out;
    assign overflow = overflow_out;
    assign flag     = (aluc == SLT || aluc == SLTU) ? 1'b1 : 1'b0;

endmodule
