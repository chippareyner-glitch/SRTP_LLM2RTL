module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    localparam [3:0] A = 4'd0;
    localparam [3:0] B = 4'd1;
    localparam [3:0] C = 4'd2;
    localparam [3:0] D = 4'd3;
    localparam [3:0] E = 4'd4;
    localparam [3:0] F = 4'd5;
    localparam [3:0] G = 4'd6;
    localparam [3:0] H = 4'd7;
    localparam [3:0] I = 4'd8;

    logic [3:0] state, next_state;

    always_ff @(posedge clk) begin
        if (!resetn) begin
            state <= A;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            A: next_state = resetn ? B : A;
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

    always_comb begin
        f = 1'b0;
        g = 1'b0;

        if (state == B) f = 1'b1;
        if (state == F || state == G || state == H) g = 1'b1;
    end

endmodule
