module TopModule (
    input  clk,
    input  resetn,
    input  x,
    input  y,
    output logic f,
    output logic g
);

    localparam logic [3:0]
        S_A  = 4'd0,  // beginning state (reset)
        S_F1 = 4'd1,  // f = 1 for one clock cycle
        S_W  = 4'd2,  // waiting for x = 1
        S_1  = 4'd3,  // got x = 1
        S_10 = 4'd4,  // got x = 1, 0
        S_G1 = 4'd5,  // got x = 1, 0, 1 -> g = 1, y check cycle 1
        S_G2 = 4'd6,  // g = 1, y check cycle 2
        S_GP = 4'd7,  // g = 1 permanently
        S_ZP = 4'd8;  // g = 0 permanently

    logic [3:0] state, next;

    always_ff @(posedge clk) begin
        if (!resetn)
            state <= S_A;
        else
            state <= next;
    end

    always_comb begin
        next = state;
        case (state)
            S_A : next = S_F1;
            S_F1: next = S_W;
            S_W : next = x ? S_1  : S_W;
            S_1 : next = x ? S_1  : S_10;
            S_10: next = x ? S_G1 : S_W;
            S_G1: next = y ? S_GP : S_G2;
            S_G2: next = y ? S_GP : S_ZP;
            S_GP: next = S_GP;
            S_ZP: next = S_ZP;
            default: next = S_A;
        endcase
    end

    always_comb begin
        f = (state == S_F1);
        g = (state == S_G1) || (state == S_G2) || (state == S_GP);
    end

endmodule
