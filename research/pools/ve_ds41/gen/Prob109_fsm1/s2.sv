module TopModule (
    input  clk,
    input  areset,
    input  in,
    output logic out
);

    logic state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= 1'b1; // B
        end else begin
            case (state)
                1'b0: begin // A
                    if (in)
                        state <= 1'b0; // A --1--> A
                    else
                        state <= 1'b1; // A --0--> B
                end
                1'b1: begin // B
                    if (in)
                        state <= 1'b1; // B --1--> B
                    else
                        state <= 1'b0; // B --0--> A
                end
                default: state <= 1'b1;
            endcase
        end
    end

    assign out = state;

endmodule
