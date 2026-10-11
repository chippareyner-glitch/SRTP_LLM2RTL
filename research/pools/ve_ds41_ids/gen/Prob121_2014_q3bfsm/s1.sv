module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic x,
    output logic z
);

    typedef enum logic [2:0] {
        S000 = 3'b000,
        S001 = 3'b001,
        S010 = 3'b010,
        S011 = 3'b011,
        S100 = 3'b100
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= S000;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        z = 1'b0;

        case (state)
            S000: begin
                z = 1'b0;
                next_state = x ? S001 : S000;
            end
            S001: begin
                z = 1'b0;
                next_state = x ? S100 : S001;
            end
            S010: begin
                z = 1'b0;
                next_state = x ? S001 : S010;
            end
            S011: begin
                z = 1'b1;
                next_state = x ? S010 : S001;
            end
            S100: begin
                z = 1'b1;
                next_state = x ? S100 : S011;
            end
            default: begin
                next_state = S000;
                z = 1'b0;
            end
        endcase
    end

endmodule
