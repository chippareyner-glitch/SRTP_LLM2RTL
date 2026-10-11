module TopModule (
    input  logic clock,
    input  logic a,
    output logic p,
    output logic q
);

    always_latch begin
        if (clock) begin
            p = a;
        end
    end

    always_latch begin
        if (!clock) begin
            q = p;
        end
    end

endmodule
