module alu (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [5:0]  aluc,
    output wire  [31:0] r,
    output wire         zero,
    output wire         carry,
    output wire         negative,
    output wire         overflow,
    output wire         flag
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

    logic [31:0] res;
    logic [32:0] sum;
    logic [32:0] diff;

    always_comb begin
        sum  = 33'b0;
        diff = 33'b0;
        case (aluc)
            ADD, ADDU: begin
                sum = {1'b0, a} + {1'b0, b};
                res = sum[31:0];
            end
            SUB, SUBU: begin
                diff = {1'b0, a} - {1'b0, b};
                res = diff[31:0];
            end
            AND:  res = a & b;
            OR:   res = a | b;
            XOR:  res = a ^ b;
            NOR:  res = ~(a | b);
            SLT:  res = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            SLTU: res = (a < b) ? 32'd1 : 32'd0;
            SLL:  res = b << a[4:0];
            SRL:  res = b >> a[4:0];
            SRA:  res = $signed(b) >>> a[4:0];
            SLLV: res = b << a[4:0];
            SRLV: res = b >> a[4:0];
            SRAV: res = $signed(b) >>> a[4:0];
            LUI:  res = {a[15:0], 16'b0};
            default: res = 32'bz;
        endcase
    end

    assign r = res;
    assign zero = (res == 32'b0);
    assign negative = res[31];
    assign carry = (aluc == ADD || aluc == ADDU) ? sum[32] :
                   (aluc == SUB || aluc == SUBU) ? ~diff[32] : 1'b0;
    assign overflow = (aluc == ADD) ? (a[31] == b[31] && res[31] != a[31]) :
                      (aluc == SUB) ? (a[31] != b[31] && res[31] != a[31]) : 1'b0;
    assign flag = (aluc == SLT || aluc == SLTU) ? res[0] : 1'bz;

endmodule
