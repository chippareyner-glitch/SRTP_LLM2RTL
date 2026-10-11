module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    logic [1:0] level;
    logic       dfr_reg;
    logic [1:0] new_level;
    logic       new_dfr;

    // Decode current water level from sensors (highest asserted sensor)
    always_comb begin
        if (s[2])      new_level = 2'b11;
        else if (s[1]) new_level = 2'b10;
        else if (s[0]) new_level = 2'b01;
        else           new_level = 2'b00;
    end

    // Determine supplemental flow valve
    always_comb begin
        if (new_level == 2'b00) begin
            new_dfr = 1'b1; // below s[0]: maximum flow
        end else if (new_level == 2'b11) begin
            new_dfr = 1'b0; // above s[2]: no flow
        end else if (new_level > level) begin
            new_dfr = 1'b1; // rising: previous level lower
        end else if (new_level < level) begin
            new_dfr = 1'b0; // falling: previous level higher
        end else begin
            new_dfr = dfr_reg; // no change: hold
        end
    end

    // State register with active-high synchronous reset
    always_ff @(posedge clk) begin
        if (reset) begin
            level   <= 2'b00;
            dfr_reg <= 1'b1;
        end else begin
            level   <= new_level;
            dfr_reg <= new_dfr;
        end
    end

    // Nominal flow outputs based on current level
    assign fr2 = (level == 2'b00) ? 1'b1 : 1'b0;
    assign fr1 = (level == 2'b00 || level == 2'b01) ? 1'b1 : 1'b0;
    assign fr0 = (level == 2'b00 || level == 2'b01 || level == 2'b10) ? 1'b1 : 1'b0;
    assign dfr = dfr_reg;

endmodule
