module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [1:0]   ena,
    input  logic [99:0]  data,
    output logic [99:0]  q
);

    initial q = 100'b0;

    always_ff @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            case (ena)
                2'b01: q <= {q[0], q[99:1]};   // rotate right by 1 bit
                2'b10: q <= {q[98:0], q[99]};  // rotate left by 1 bit
                default: q <= q;               // 2'b00 or 2'b11: no rotate
            endcase
        end
    end

endmodule
