module TopModule (
    input  clk,
    input  reset,
    input  x,
    output logic z
);

    logic [2:0] state;
    logic [2:0] next_state;
    logic       z_comb;

    // Next-state logic
    always_comb begin
        case (state)
            3'b000: next_state = x ? 3'b001 : 3'b000;
            3'b001: next_state = x ? 3'b100 : 3'b001;
            3'b010: next_state = x ? 3'b001 : 3'b010;
            3'b011: next_state = x ? 3'b010 : 3'b001;
            3'b100: next_state = x ? 3'b100 : 3'b011;
            default: next_state = 3'b000;
        endcase
    end

    // Moore output as a function of the present state
    always_comb begin
        case (state)
            3'b011:  z_comb = 1'b1;
            3'b100:  z_comb = 1'b1;
            default: z_comb = 1'b0;
        endcase
    end

    // State and registered output update on the positive clock edge.
    // z is registered, so it reflects the previous state one cycle later.
    always_ff @(posedge clk) begin
        if (reset) begin
            state <= 3'b000;
            z     <= 1'b0;
        end else begin
            state <= next_state;
            z     <= z_comb;
        end
    end

endmodule
