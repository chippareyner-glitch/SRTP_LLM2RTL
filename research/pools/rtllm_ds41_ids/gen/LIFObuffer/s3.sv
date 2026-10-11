module LIFObuffer (
    input  logic [3:0] dataIn,
    input  logic       RW,
    input  logic       EN,
    input  logic       Rst,
    input  logic       Clk,
    output wire        EMPTY,
    output wire        FULL,
    output logic [3:0] dataOut
);

    logic [3:0] stack_mem [0:3];
    logic [2:0] SP;
    integer i;

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                SP <= 3'd4;
                dataOut <= 4'd0;
                for (i = 0; i < 4; i = i + 1) begin
                    stack_mem[i] <= 4'd0;
                end
            end else begin
                if (RW == 1'b0) begin
                    if (SP != 3'd0) begin
                        stack_mem[SP - 3'd1] <= dataIn;
                        SP <= SP - 3'd1;
                    end
                end else begin
                    if (SP != 3'd4) begin
                        dataOut <= stack_mem[SP];
                        stack_mem[SP] <= 4'd0;
                        SP <= SP + 3'd1;
                    end
                end
            end
        end
    end

    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

endmodule
