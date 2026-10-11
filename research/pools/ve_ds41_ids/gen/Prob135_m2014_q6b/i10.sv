module TopModule (
    input  logic [2:0] y,
    input  logic       w,
    output logic       Y1
);
    always_comb begin
        case (y)
            3'b000: Y1 = 1'b0; // A
            3'b001: Y1 = 1'b1; // B
            3'b010: Y1 = w;    // C
            3'b011: Y1 = 1'b0; // D
            3'b100: Y1 = w;    // E
            3'b101: Y1 = 1'b1; // F
            default: Y1 = 1'b0;
        endcase
    end
endmodule
