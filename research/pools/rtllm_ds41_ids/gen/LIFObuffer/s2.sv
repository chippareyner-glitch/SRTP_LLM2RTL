module LIFObuffer (
    input  logic [3:0] dataIn,
    input  logic       RW,
    input  logic       EN,
    input  logic       Rst,
    input  logic       Clk,
    output logic       EMPTY,
    output logic       FULL,
    output logic [3:0] dataOut
);

    logic [3:0] stack_mem [0:3];
    logic [2:0] SP;
    integer i;

    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                SP <= 3'd4;
                for (i = 0; i < 4; i = i + 1) begin
                    stack_mem[i] <= 4'b0000;
                end
                dataOut <= 4'b0000;
            end else begin
                if (!RW && !FULL) begin
                    stack_mem[SP - 1'b1] <= dataIn;
                    SP <= SP - 1'b1;
                end else if (RW && !EMPTY) begin
                    dataOut <= stack_mem[SP];
                    stack_mem[SP] <= 4'b0000;
                    SP <= SP + 1'b1;
                end
            end
        end
    end

endmodule
