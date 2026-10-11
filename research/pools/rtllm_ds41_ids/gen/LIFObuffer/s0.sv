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

    logic [2:0] SP;
    logic [3:0] stack_mem [0:3];
    integer i;

    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                SP <= 3'd4;
                for (i = 0; i < 4; i = i + 1) begin
                    stack_mem[i] <= 4'd0;
                end
            end
            else begin
                if (!RW) begin
                    if (SP != 3'd0) begin
                        stack_mem[SP - 1] <= dataIn;
                        SP <= SP - 1;
                    end
                end
                else begin
                    if (SP != 3'd4) begin
                        dataOut <= stack_mem[SP];
                        stack_mem[SP] <= 4'd0;
                        SP <= SP + 1;
                    end
                end
            end
        end
    end

endmodule
