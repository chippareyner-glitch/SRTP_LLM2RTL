module TopModule (
    input  logic clk,
    input  logic reset,
    output logic shift_ena
);

    logic [2:0] count;

    always_ff @(posedge clk) begin
        if (reset)
            count <= 3'd4;
        else if (count > 0)
            count <= count - 1;
    end

    assign shift_ena = (count > 0);

endmodule
