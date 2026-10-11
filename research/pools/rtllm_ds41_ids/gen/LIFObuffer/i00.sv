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

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                SP <= 3'd4;
                for (i = 0; i < 4; i = i + 1) begin
                    stack_mem[i] <= 4'b0000;
                end
                EMPTY <= 1'b1;
                FULL  <= 1'b0;
            end else begin
                if (!RW) begin
                    // Write operation
                    if (!FULL) begin
                        stack_mem[SP - 1] <= dataIn;
                        SP <= SP - 1;
                        EMPTY <= 1'b0;
                        FULL  <= (SP - 1 == 3'd0) ? 1'b1 : 1'b0;
                    end
                end else begin
                    // Read operation
                    if (!EMPTY) begin
                        dataOut <= stack_mem[SP];
                        stack_mem[SP] <= 4'b0000;
                        SP <= SP + 1;
                        FULL  <= 1'b0;
                        EMPTY <= (SP + 1 == 3'd4) ? 1'b1 : 1'b0;
                    end
                end
            end
        end
    end

endmodule
