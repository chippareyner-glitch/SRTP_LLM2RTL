module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    logic [2:0] current_level;
    logic [2:0] prev_level;

    always_ff @(posedge clk) begin
        if (reset) begin
            current_level <= 3'b000;
            prev_level    <= 3'b000;
        end else begin
            if (s != current_level) begin
                prev_level    <= current_level;
                current_level <= s;
            end
        end
    end

    always_comb begin
        fr0 = (current_level != 3'b111) ? 1'b1 : 1'b0;
        fr1 = (current_level == 3'b000 || current_level == 3'b001) ? 1'b1 : 1'b0;
        fr2 = (current_level == 3'b000) ? 1'b1 : 1'b0;
        if (current_level == 3'b111) begin
            dfr = 1'b0;
        end else if (current_level == 3'b000) begin
            dfr = 1'b1;
        end else begin
            dfr = (prev_level < current_level) ? 1'b1 : 1'b0;
        end
    end

endmodule
