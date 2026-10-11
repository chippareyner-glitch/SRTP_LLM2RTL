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

    // Stack memory: 4 entries of 4 bits each
    logic [3:0] stack_mem [0:3];

    // Stack pointer: 4 = empty, 0 = full (4 entries held)
    logic [2:0] SP;

    integer i;

    // Status flags derived from the stack pointer
    assign EMPTY = (SP == 3'd4);
    assign FULL  = (SP == 3'd0);

    // Combinational data output: current top of stack (the entry being popped this cycle).
    // SP[1:0] is a safe bounded index; EMPTY forces the output to zero.
    assign dataOut = EMPTY ? 4'b0000 : stack_mem[SP[1:0]];

    always_ff @(posedge Clk) begin
        if (EN) begin
            if (Rst) begin
                // Synchronous active-high reset: clear stack and pointer
                SP <= 3'd4;
                for (i = 0; i < 4; i = i + 1) begin
                    stack_mem[i] <= 4'b0000;
                end
            end
            else begin
                if (!RW && !FULL) begin
                    // Write (push): store at new top location then decrement SP
                    stack_mem[SP - 3'd1] <= dataIn;
                    SP <= SP - 3'd1;
                end
                else if (RW && !EMPTY) begin
                    // Read (pop): clear the popped entry then increment SP
                    stack_mem[SP[1:0]] <= 4'b0000;
                    SP <= SP + 3'd1;
                end
            end
        end
    end

endmodule
