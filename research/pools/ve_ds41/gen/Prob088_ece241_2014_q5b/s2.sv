module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    logic [1:0] state;
    localparam logic [1:0] A = 2'b01;
    localparam logic [1:0] B = 2'b10;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= A;
        end else begin
            state[0] <= state[0] & ~x;
            state[1] <= (state[0] & x) | state[1];
        end
    end

    assign z = (state[0] & x) | (state[1] & ~x);

endmodule
