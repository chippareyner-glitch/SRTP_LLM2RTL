module TopModule (
    input clk,
    input x,
    input [2:0] y,
    output Y0,
    output z
);

    logic [2:0] Y;

    always_comb begin
        case (y)
            3'b000: Y = x ? 3'b001 : 3'b000;
            3'b001: Y = x ? 3'b100 : 3'b001;
            3'b010: Y = x ? 3'b001 : 3'b010;
            3'b011: Y = x ? 3'b010 : 3'b001;
            3'b100: Y = x ? 3'b100 : 3'b011;
            default: Y = y; // Undefined states 101, 110, 111: self-loop
        endcase
    end

    assign Y0 = Y[0];

    assign z = (y == 3'b011) || (y == 3'b100);

endmodule
