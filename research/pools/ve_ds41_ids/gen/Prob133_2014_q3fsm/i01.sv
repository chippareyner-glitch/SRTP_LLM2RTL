module TopModule (
    input  clk,
    input  reset,
    input  s,
    input  w,
    output logic z
);

    typedef enum logic [1:0] {
        A = 2'b00,
        B = 2'b01,
        C = 2'b10,
        D = 2'b11
    } state_t;

    state_t state, next_state;
    logic [1:0] count;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
            count <= 2'b00;
            z <= 1'b0;
        end else begin
            state <= next_state;
            case (state)
                A: begin
                    count <= 2'b00;
                    z <= 1'b0;
                end
                B: begin
                    count <= {1'b0, w};
                    z <= 1'b0;
                end
                C: begin
                    count <= count + w;
                    z <= 1'b0;
                end
                D: begin
                    if (count + w == 2'b10)
                        z <= 1'b1;
                    else
                        z <= 1'b0;
                    count <= count + w;
                end
                default: begin
                    count <= 2'b00;
                    z <= 1'b0;
                end
            endcase
        end
    end

    always_comb begin
        case (state)
            A: next_state = s ? B : A;
            B: next_state = C;
            C: next_state = D;
            D: next_state = B;
            default: next_state = A;
        endcase
    end

endmodule
