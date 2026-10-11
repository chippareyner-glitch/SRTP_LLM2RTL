module TopModule(
    input  clk,
    input  reset,
    input  w,
    output z
);

    localparam [2:0] A = 3'd0;
    localparam [2:0] B = 3'd1;
    localparam [2:0] C = 3'd2;
    localparam [2:0] D = 3'd3;
    localparam [2:0] E = 3'd4;
    localparam [2:0] F = 3'd5;

    reg [2:0] state;
    reg [2:0] next_state;

    // State table
    always @(*) begin
        case (state)
            A: begin
                if (w) next_state = B;
                else   next_state = A;
            end
            B: begin
                if (w) next_state = C;
                else   next_state = D;
            end
            C: begin
                if (w) next_state = E;
                else   next_state = D;
            end
            D: begin
                if (w) next_state = F;
                else   next_state = A;
            end
            E: begin
                if (w) next_state = E;
                else   next_state = D;
            end
            F: begin
                if (w) next_state = C;
                else   next_state = D;
            end
            default: next_state = A;
        endcase
    end

    // State flip-flops
    always @(posedge clk) begin
        if (reset)
            state <= A;
        else
            state <= next_state;
    end

    // Moore output
    assign z = (state == E) || (state == F);

endmodule
