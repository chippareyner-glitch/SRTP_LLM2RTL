module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    localparam logic [1:0] A  = 2'd0;
    localparam logic [1:0] B0 = 2'd1;
    localparam logic [1:0] B1 = 2'd2;
    localparam logic [1:0] B2 = 2'd3;

    logic [1:0] state, next_state;
    logic [1:0] cnt;

    always_comb begin
        next_state = state;
        case (state)
            A:  if (s) next_state = B0;
            B0: next_state = B1;
            B1: next_state = B2;
            B2: next_state = B0;
            default: next_state = A;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= A;
            cnt   <= 2'd0;
            z     <= 1'b0;
        end else begin
            state <= next_state;
            case (state)
                A: begin
                    cnt <= 2'd0;
                    z   <= 1'b0;
                end
                B0: begin
                    cnt <= w;
                    z   <= 1'b0;
                end
                B1: begin
                    cnt <= cnt + w;
                    z   <= 1'b0;
                end
                B2: begin
                    z   <= (cnt + w == 2) ? 1'b1 : 1'b0;
                    cnt <= 2'd0;
                end
                default: begin
                    cnt <= 2'd0;
                    z   <= 1'b0;
                end
            endcase
        end
    end

endmodule
