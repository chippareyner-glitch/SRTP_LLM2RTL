module TopModule (
    input  logic       clk,
    input  logic       x,
    input  logic [2:0] y,
    output logic       Y0,
    output logic       z
);

    logic next_Y0;
    logic next_z;

    always_comb begin
        next_Y0 = 1'b0;
        next_z  = 1'b0;

        case (y)
            3'b000: begin
                next_Y0 = x ? 1'b1 : 1'b0;
                next_z  = 1'b0;
            end
            3'b001: begin
                next_Y0 = x ? 1'b0 : 1'b1;
                next_z  = 1'b0;
            end
            3'b010: begin
                next_Y0 = x ? 1'b1 : 1'b0;
                next_z  = 1'b0;
            end
            3'b011: begin
                next_Y0 = x ? 1'b0 : 1'b1;
                next_z  = 1'b1;
            end
            3'b100: begin
                next_Y0 = x ? 1'b0 : 1'b1;
                next_z  = 1'b1;
            end
            default: begin
                next_Y0 = 1'b0;
                next_z  = 1'b0;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        Y0 <= next_Y0;
        z  <= next_z;
    end

endmodule
