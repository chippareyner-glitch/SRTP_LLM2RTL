module TopModule (
    input  logic       clk,
    input  logic       resetn,
    input  logic [2:0] r,
    output logic [2:0] g
);

    typedef enum logic [1:0] {
        A = 2'b00,
        B = 2'b01,
        C = 2'b10,
        D = 2'b11
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            A: begin
                if (r[0])       next_state = B;
                else if (r[1])  next_state = C;
                else if (r[2])  next_state = D;
                else            next_state = A;
            end
            B: begin
                if (r[0])       next_state = B;
                else            next_state = A;
            end
            C: begin
                if (r[1])       next_state = C;
                else            next_state = A;
            end
            D: begin
                if (r[2])       next_state = D;
                else            next_state = A;
            end
            default:            next_state = A;
        endcase
    end

    always_ff @(posedge clk) begin
        if (!resetn) state <= A;
        else         state <= next_state;
    end

    always_comb begin
        case (state)
            B:       g = 3'b001;
            C:       g = 3'b010;
            D:       g = 3'b100;
            default: g = 3'b000;
        endcase
    end

endmodule
