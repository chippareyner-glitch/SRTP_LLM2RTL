module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    localparam logic [3:0] A = 4'd0;
    localparam logic [3:0] B = 4'd1;
    localparam logic [3:0] C = 4'd2;
    localparam logic [3:0] D = 4'd3;
    localparam logic [3:0] E = 4'd4;
    localparam logic [3:0] F = 4'd5;
    localparam logic [3:0] G = 4'd6;
    localparam logic [3:0] H = 4'd7;
    localparam logic [3:0] I = 4'd8;

    logic [3:0] state, next_state;

    always_ff @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            A: next_state = B;
            B: next_state = C;
            C: next_state = x ? D : C;
            D: next_state = x ? D : E;
            E: next_state = x ? F : C;
            F: next_state = y ? H : G;
            G: next_state = y ? H : I;
            H: next_state = H;
            I: next_state = I;
            default: next_state = A;
        endcase
    end

    assign f = (state == B);
    assign g = (state == F) || (state == G) || (state == H);

endmodule
