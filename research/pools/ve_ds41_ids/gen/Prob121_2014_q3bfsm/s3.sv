module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic x,
    output logic z
);

    logic [2:0] y;
    logic [2:0] y_next;

    always_comb begin
        y_next = 3'b000;
        z = 1'b0;

        case (y)
            3'b000: begin
                y_next = x ? 3'b001 : 3'b000;
                z = 1'b0;
            end
            3'b001: begin
                y_next = x ? 3'b100 : 3'b001;
                z = 1'b0;
            end
            3'b010: begin
                y_next = x ? 3'b001 : 3'b010;
                z = 1'b0;
            end
            3'b011: begin
                y_next = x ? 3'b010 : 3'b001;
                z = 1'b1;
            end
            3'b100: begin
                y_next = x ? 3'b100 : 3'b011;
                z = 1'b1;
            end
            default: begin
                y_next = 3'b000;
                z = 1'b0;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            y <= 3'b000;
        else
            y <= y_next;
    end

endmodule
