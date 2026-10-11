module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    typedef enum logic [2:0] {
        S0, // below s0
        S1, // between s1 and s0, rising
        S2, // between s1 and s0, falling
        S3, // between s2 and s1, rising
        S4, // between s2 and s1, falling
        S5  // above s2
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        case (state)
            S0: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S1;
                    3'b011: next_state = S3;
                    3'b111: next_state = S5;
                    default: next_state = S0;
                endcase
            end
            S1: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S1;
                    3'b011: next_state = S3;
                    3'b111: next_state = S5;
                    default: next_state = S1;
                endcase
            end
            S2: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S2;
                    3'b011: next_state = S3;
                    3'b111: next_state = S5;
                    default: next_state = S2;
                endcase
            end
            S3: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S2;
                    3'b011: next_state = S3;
                    3'b111: next_state = S5;
                    default: next_state = S3;
                endcase
            end
            S4: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S2;
                    3'b011: next_state = S4;
                    3'b111: next_state = S5;
                    default: next_state = S4;
                endcase
            end
            S5: begin
                case (s)
                    3'b000: next_state = S0;
                    3'b001: next_state = S2;
                    3'b011: next_state = S4;
                    3'b111: next_state = S5;
                    default: next_state = S5;
                endcase
            end
            default: next_state = S0;
        endcase
    end

    always_comb begin
        case (state)
            S0: {fr2, fr1, fr0, dfr} = 4'b1111;
            S1: {fr2, fr1, fr0, dfr} = 4'b0111;
            S2: {fr2, fr1, fr0, dfr} = 4'b0110;
            S3: {fr2, fr1, fr0, dfr} = 4'b0011;
            S4: {fr2, fr1, fr0, dfr} = 4'b0010;
            S5: {fr2, fr1, fr0, dfr} = 4'b0000;
            default: {fr2, fr1, fr0, dfr} = 4'b1111;
        endcase
    end

endmodule
