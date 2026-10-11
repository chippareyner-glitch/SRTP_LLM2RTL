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
    logic dfr_reg;

    logic [1:0] next_level;
    always_comb begin
        case (s)
            3'b000: next_level = 2'd0;
            3'b001: next_level = 2'd1;
            3'b011: next_level = 2'd2;
            3'b111: next_level = 2'd3;
            default: next_level = level;
        endcase
    end

    logic next_dfr;
    always_comb begin
        if (next_level == 2'd0)
            next_dfr = 1'b1;
        else if (next_level == 2'd3)
            next_dfr = 1'b0;
        else if (next_level > level)
            next_dfr = 1'b1;
        else if (next_level < level)
            next_dfr = 1'b0;
        else
            next_dfr = dfr_reg;
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            level   <= 2'd0;
            dfr_reg <= 1'b1;
        end else begin
            level   <= next_level;
            dfr_reg <= next_dfr;
        end
    end

    always_comb begin
        case (level)
            2'd0: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd1: begin
                fr2 = 1'b0;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd2: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b1;
            end
            2'd3: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end
            default: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end
        endcase
        dfr = dfr_reg;
    end

endmodule
