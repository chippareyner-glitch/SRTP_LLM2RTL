module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    typedef enum logic [3:0] {
        A,
        F,
        S0,
        S1,
        S2,
        G1,
        G2,
        GPERM,
        FAIL
    } state_t;

    state_t state;

    always_ff @(posedge clk) begin
        if (!resetn) begin
            state <= A;
        end else begin
            case (state)
                A:      state <= F;
                F:      state <= S0;
                S0:     state <= x ? S1 : S0;
                S1:     state <= x ? S1 : S2;
                S2:     state <= x ? G1 : S0;
                G1:     state <= y ? GPERM : G2;
                G2:     state <= y ? GPERM : FAIL;
                GPERM:  state <= GPERM;
                FAIL:   state <= FAIL;
                default: state <= A;
            endcase
        end
    end

    always_comb begin
        f = 1'b0;
        g = 1'b0;
        case (state)
            F:             f = 1'b1;
            G1, G2, GPERM: g = 1'b1;
            default: begin
                f = 1'b0;
                g = 1'b0;
            end
        endcase
    end

endmodule
