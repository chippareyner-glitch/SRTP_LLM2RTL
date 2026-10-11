module LIFObuffer(
    input  [3:0] dataIn,
    input        RW,
    input        EN,
    input        Rst,
    input        Clk,
    output       EMPTY,
    output       FULL,
    output reg [3:0] dataOut
);

    reg [3:0] stack_mem [0:3];
    reg [2:0] SP;
    integer i;

    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

    always @(posedge Clk or posedge Rst) begin
        if (Rst) begin
            SP <= 3'd4;
            for (i = 0; i < 4; i = i + 1) begin
                stack_mem[i] <= 4'b0000;
            end
        end else if (EN) begin
            if (RW == 1'b0) begin
                if (!FULL) begin
                    stack_mem[SP - 1] <= dataIn;
                    SP <= SP - 1;
                end
            end else begin
                if (!EMPTY) begin
                    dataOut <= stack_mem[SP];
                    stack_mem[SP] <= 4'b0000;
                    SP <= SP + 1;
                end
            end
        end
    end

endmodule
