module TopModule (
    input  in,
    input  [3:0] state,
    output reg [3:0] next_state,
    output reg out
);

    always @(*) begin
        // Defaults for invalid states: override one-hot equations
        next_state = 4'b0000;
        out = 1'b0;

        case (state)
            // A = 4'b0001
            4'b0001: begin
                next_state = in ? 4'b0010 : 4'b0001;
                out = 1'b0;
            end

            // B = 4'b0010
            4'b0010: begin
                next_state = in ? 4'b0010 : 4'b0100;
                out = 1'b0;
            end

            // C = 4'b0100
            4'b0100: begin
                next_state = in ? 4'b1000 : 4'b0001;
                out = 1'b0;
            end

            // D = 4'b1000
            4'b1000: begin
                next_state = in ? 4'b0010 : 4'b0100;
                out = 1'b1;
            end

            // Invalid one-hot states
            default: begin
                next_state = 4'b0000;
                out = 1'b0;
            end
        endcase
    end

endmodule
