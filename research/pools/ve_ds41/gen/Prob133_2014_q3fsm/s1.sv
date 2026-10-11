module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    localparam logic [2:0] A    = 3'd0,
                           B0_0 = 3'd1,
                           B0_1 = 3'd2,
                           B1_0 = 3'd3,
                           B1_1 = 3'd4,
                           B2_0 = 3'd5,
                           B2_1 = 3'd6,
                           B2_2 = 3'd7;

    logic [2:0] state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            A:         next_state = s ? B0_0 : A;
            B0_0, B0_1: next_state = w ? B1_1 : B1_0;
            B1_0:      next_state = w ? B2_1 : B2_0;
            B1_1:      next_state = w ? B2_2 : B2_1;
            B2_0:      next_state = B0_0;
            B2_1:      next_state = w ? B0_1 : B0_0;
            B2_2:      next_state = w ? B0_0 : B0_1;
            default:   next_state = A;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) state <= A;
        else       state <= next_state;
    end

    assign z = (state == B0_1);

endmodule
