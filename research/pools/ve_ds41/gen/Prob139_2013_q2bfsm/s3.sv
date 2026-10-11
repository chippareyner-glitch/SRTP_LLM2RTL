module TopModule (
    input  clk,
    input  resetn,
    input  x,
    input  y,
    output f,
    output g
);

    localparam A = 4'd0;
    localparam B = 4'd1;
    localparam C = 4'd2;
    localparam D = 4'd3;
    localparam E = 4'd4;
    localparam F = 4'd5;
    localparam G = 4'd6;
    localparam H = 4'd7;
    localparam I = 4'd8;

    logic [3:0] state, next;

    always @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next;
    end

    always @(*) begin
        case (state)
            A: next = resetn ? B : A;
            B: next = C;
            C: next = x ? D : C;
            D: next = x ? D : E;
            E: next = x ? F : C;
            F: next = y ? G : H;
            G: next = G;
            H: next = y ? G : I;
            I: next = I;
            default: next = A;
        endcase
    end

    assign f = (state == B);
    assign g = (state == F) || (state == G) || (state == H);

endmodule
