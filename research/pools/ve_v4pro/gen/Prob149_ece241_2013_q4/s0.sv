module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    localparam [1:0] LVL_BELOW   = 2'b00; // Below s[0]
    localparam [1:0] LVL_S0_S1   = 2'b01; // Between s[1] and s[0]
    localparam [1:0] LVL_S1_S2   = 2'b10; // Between s[2] and s[1]
    localparam [1:0] LVL_ABOVE   = 2'b11; // Above s[2]

    logic [1:0] level, prev_level, next_level;

    // Decode current water level from sensor inputs.
    always_comb begin
        case (s)
            3'b000:  next_level = LVL_BELOW;
            3'b001:  next_level = LVL_S0_S1;
            3'b011:  next_level = LVL_S1_S2;
            3'b111:  next_level = LVL_ABOVE;
            default: next_level = level; // Invalid sensor pattern: hold current level
        endcase
    end

    // State memory: current water level and previous level before last change.
    always_ff @(posedge clk) begin
        if (reset) begin
            level      <= LVL_BELOW;
            prev_level <= LVL_BELOW;
        end else begin
            if (next_level != level) begin
                prev_level <= level;
                level      <= next_level;
            end
        end
    end

    // Nominal flow rate outputs.
    assign fr2 = (level == LVL_BELOW);
    assign fr1 = (level == LVL_BELOW) || (level == LVL_S0_S1);
    assign fr0 = (level == LVL_BELOW) || (level == LVL_S0_S1) || (level == LVL_S1_S2);

    // Supplemental flow valve: open below s[0], or when the water level has risen
    // (previous level lower than current) and we are not already above s[2].
    assign dfr = (level == LVL_BELOW) ||
                 ((level != LVL_ABOVE) && (prev_level < level));

endmodule
