module TopModule (
    input clk,
    input reset,
    input [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    logic [1:0] level;
    logic [1:0] prev_level;

    always_comb begin
        if (s[2]) level = 2'd3;
        else if (s[1]) level = 2'd2;
        else if (s[0]) level = 2'd1;
        else level = 2'd0;
    end

    always_ff @(posedge clk) begin
        if (reset) prev_level <= 2'd0;
        else prev_level <= level;
    end

    assign fr2 = (level == 2'd0);
    assign fr1 = (level == 2'd0) || (level == 2'd1);
    assign fr0 = (level != 2'd3);
    assign dfr = (level > prev_level);

endmodule
