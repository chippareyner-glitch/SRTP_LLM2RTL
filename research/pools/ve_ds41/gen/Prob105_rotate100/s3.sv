module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [1:0]   ena,
    input  logic [99:0]  data,
    output logic [99:0]  q
);

    always_ff @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            case (ena)
                2'b01: q <= {q[0], q[99:1]};   // rotate right by 1
                2'b10: q <= {q[98:0], q[99]};  // rotate left by 1
                default: q <= q;
            endcase
        end
    end

endmodule
