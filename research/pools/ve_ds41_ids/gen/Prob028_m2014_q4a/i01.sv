module TopModule (
    input  logic d,
    input  logic ena,
    output logic q
);

    always_ff @(posedge ena) begin
        q <= d;
    end

endmodule
