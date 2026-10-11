module TopModule (
    input  logic        clk,
    input  logic        load,
    input  logic        ena,
    input  logic [1:0]  amount,
    input  logic [63:0] data,
    output logic [63:0] q
);

    logic [63:0] q_reg;

    initial q_reg = 64'b0;

    always_ff @(posedge clk) begin
        if (load) begin
            q_reg <= data;
        end else if (ena) begin
            case (amount)
                2'b00: q_reg <= {q_reg[62:0], 1'b0};
                2'b01: q_reg <= {q_reg[55:0], 8'b0};
                2'b10: q_reg <= {q_reg[63], q_reg[63:1]};
                2'b11: q_reg <= {{8{q_reg[63]}}, q_reg[63:8]};
                default: q_reg <= q_reg;
            endcase
        end
    end

    assign q = q_reg;

endmodule
