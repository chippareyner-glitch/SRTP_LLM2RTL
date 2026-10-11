module LIFObuffer (
    input  logic       Clk,
    input  logic       Rst,
    input  logic       EN,
    input  logic       RW,
    input  logic [3:0] dataIn,
    output logic       EMPTY,
    output logic       FULL,
    output logic [3:0] dataOut
);

    logic [3:0] stack_mem [0:3];
    logic [2:0] SP;

    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                SP <= 3'd4;
                for (int i = 0; i < 4; i++) begin
                    stack_mem[i] <= 4'd0;
                end
            end
            else begin
                if (!RW) begin
                    if (!FULL) begin
                        SP <= SP - 3'd1;
                        stack_mem[SP - 3'd1] <= dataIn;
                    end
                end
                else begin
                    if (!EMPTY) begin
                        dataOut <= stack_mem[SP];
                        stack_mem[SP] <= 4'd0;
                        SP <= SP + 3'd1;
                    end
                end
            end
        end
    end

endmodule
