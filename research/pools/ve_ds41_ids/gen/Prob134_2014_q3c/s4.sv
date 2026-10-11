module TopModule (
    input  logic clk,
    input  logic x,
    input  logic [2:0] y,
    output logic Y0,
    output logic z
);

    logic [2:0] Y;
    logic z_out;

    always_comb begin
        z_out = 1'b0;
        case (y)
            3'b000: Y = x ? 3'b001 : 3'b000;
            3'b001: Y = x ? 3'b100 : 3'b001;
            3'b010: Y = x ? 3'b001 : 3'b010;
            3'b011: begin
                Y = x ? 3'b010 : 3'b001;
                z_out = 1'b1;
            end
            3'b100: begin
                Y = x ? 3'b100 : 3'b011;
                z_out = 1'b1;
            end
            default: Y = 3'b000;
        endcase
    end

    assign Y0 = Y[0];
    assign z  = z_out;

endmodule
