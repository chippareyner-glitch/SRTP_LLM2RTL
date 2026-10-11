module TopModule (
    input  clk,
    input  reset,
    output logic shift_ena
);

    reg [2:0] cnt;

    always @(posedge clk) begin
        if (reset)
            cnt <= 3'd0;
        else if (cnt < 3'd4)
            cnt <= cnt + 1'b1;
    end

    assign shift_ena = (cnt < 3'd4);

endmodule
