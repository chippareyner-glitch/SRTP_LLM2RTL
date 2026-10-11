module TopModule (
    input clk,
    input reset,
    input [2:0] s,
    output fr2,
    output fr1,
    output fr0,
    output dfr
);

    localparam B = 2'd0;
    localparam L = 2'd1;
    localparam M = 2'd2;
    localparam H = 2'd3;

    logic [1:0] state, next;

    always_comb begin
        case (s)
            3'b000: next = B;
            3'b001: next = L;
            3'b011: next = M;
            3'b111: next = H;
            default: next = B;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) state <= B;
        else state <= next;
    end

    assign fr2 = (next == B);
    assign fr1 = (next == B) || (next == L);
    assign fr0 = (next == B) || (next == L) || (next == M);
    assign dfr = (next == B) || ((next > state) && (next != H));

endmodule
