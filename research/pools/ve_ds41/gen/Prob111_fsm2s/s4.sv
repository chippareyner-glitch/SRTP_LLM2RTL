module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic j,
    input  logic k,
    output logic out
);

    localparam logic OFF = 1'b0;
    localparam logic ON  = 1'b1;

    logic state, next_state;

    always_comb begin
        next_state = state;

        case (state)
            OFF: begin
                if (j)
                    next_state = ON;
                else
                    next_state = OFF;
            end
            ON: begin
                if (k)
                    next_state = OFF;
                else
                    next_state = ON;
            end
            default: next_state = OFF;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= OFF;
        else
            state <= next_state;
    end

    assign out = (state == ON);

endmodule
