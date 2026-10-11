module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    logic [1:0] curr_level;
    logic [1:0] prev_level;
    logic [1:0] new_level;

    always_comb begin
        case (s)
            3'b111: new_level = 2'd3;
            3'b011: new_level = 2'd2;
            3'b001: new_level = 2'd1;
            default: new_level = 2'd0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            curr_level <= 2'd0;
            prev_level <= 2'd0;
        end else begin
            if (new_level != curr_level) begin
                prev_level <= curr_level;
                curr_level <= new_level;
            end
        end
    end

    always_comb begin
        case (curr_level)
            2'd0: begin fr2 = 1'b1; fr1 = 1'b1; fr0 = 1'b1; end
            2'd1: begin fr2 = 1'b0; fr1 = 1'b1; fr0 = 1'b1; end
            2'd2: begin fr2 = 1'b0; fr1 = 1'b0; fr0 = 1'b1; end
            2'd3: begin fr2 = 1'b0; fr1 = 1'b0; fr0 = 1'b0; end
            default: begin fr2 = 1'b0; fr1 = 1'b0; fr0 = 1'b0; end
        endcase

        if (curr_level == 2'd0)
            dfr = 1'b1;
        else if (curr_level == 2'd3)
            dfr = 1'b0;
        else
            dfr = (curr_level > prev_level) ? 1'b1 : 1'b0;
    end

endmodule
