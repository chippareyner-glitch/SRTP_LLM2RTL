module alu(
    input  [31:0] a,
    input  [31:0] b,
    input  [5:0]  aluc,
    output reg [31:0] r,
    output reg zero,
    output reg carry,
    output reg negative,
    output reg overflow,
    output reg flag
);

    parameter [5:0] ADD   = 6'b100000;
    parameter [5:0] ADDU  = 6'b100001;
    parameter [5:0] SUB   = 6'b100010;
    parameter [5:0] SUBU  = 6'b100011;
    parameter [5:0] AND   = 6'b100100;
    parameter [5:0] OR    = 6'b100101;
    parameter [5:0] XOR   = 6'b100110;
    parameter [5:0] NOR   = 6'b100111;
    parameter [5:0] SLT   = 6'b101010;
    parameter [5:0] SLTU  = 6'b101011;
    parameter [5:0] SLL   = 6'b000000;
    parameter [5:0] SRL   = 6'b000010;
    parameter [5:0] SRA   = 6'b000011;
    parameter [5:0] SLLV  = 6'b000100;
    parameter [5:0] SRLV  = 6'b000110;
    parameter [5:0] SRAV  = 6'b000111;
    parameter [5:0] LUI   = 6'b001111;

    wire signed [31:0] a_signed;
    wire signed [31:0] b_signed;
    reg  [32:0]        temp;

    assign a_signed = a;
    assign b_signed = b;

    always @(*) begin
        r        = 32'b0;
        carry    = 1'b0;
        overflow = 1'b0;
        flag     = 1'bz;
        temp     = 33'b0;

        case (aluc)
            ADD, ADDU: begin
                temp     = {1'b0, a} + {1'b0, b};
                r        = temp[31:0];
                carry    = temp[32];
                overflow = (a[31] == b[31]) && (r[31] != a[31]);
            end

            SUB, SUBU: begin
                temp     = {1'b0, a} + {1'b0, ~b} + 33'd1;
                r        = temp[31:0];
                carry    = temp[32];
                overflow = (a[31] != b[31]) && (r[31] != a[31]);
            end

            AND: r = a & b;
            OR:  r = a | b;
            XOR: r = a ^ b;
            NOR: r = ~(a | b);

            SLT: begin
                r    = (a_signed < b_signed) ? 32'd1 : 32'd0;
                flag = r[0];
            end

            SLTU: begin
                r    = (a < b) ? 32'd1 : 32'd0;
                flag = r[0];
            end

            SLL:  r = b << a[4:0];
            SRL:  r = b >> a[4:0];
            SRA:  r = b_signed >>> a[4:0];

            SLLV: r = b << a[4:0];
            SRLV: r = b >> a[4:0];
            SRAV: r = b_signed >>> a[4:0];

            LUI:  r = {a[15:0], 16'b0};

            default: begin
                r        = 32'bz;
                carry    = 1'b0;
                overflow = 1'b0;
                flag     = 1'bz;
            end
        endcase

        zero     = (r == 32'b0);
        negative = r[31];
    end

endmodule
