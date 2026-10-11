module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    typedef enum logic [3:0] {
        A     = 4'd0,
        B0    = 4'd1,
        B1_0  = 4'd2,
        B1_1  = 4'd3,
        B2_0  = 4'd4,
        B2_1  = 4'd5,
        B2_2  = 4'd6,
        OUT1  = 4'd7,
        OUT0  = 4'd8
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        case (state)
            A: begin
                if (s) next_state = B0;
                else   next_state = A;
            end
            B0: begin
                if (w) next_state = B1_1;
                else   next_state = B1_0;
            end
            B1_0: begin
                if (w) next_state = B2_1;
                else   next_state = B2_0;
            end
            B1_1: begin
                if (w) next_state = B2_2;
                else   next_state = B2_1;
            end
            B2_0: begin
                next_state = OUT0;
            end
            B2_1: begin
                if (w) next_state = OUT1;
                else   next_state = OUT0;
            end
            B2_2: begin
                if (w) next_state = OUT0;
                else   next_state = OUT1;
            end
            OUT1: begin
                next_state = B0;
            end
            OUT0: begin
                next_state = B0;
            end
            default: next_state = A;
        endcase
    end

    assign z = (state == OUT1);

endmodule
