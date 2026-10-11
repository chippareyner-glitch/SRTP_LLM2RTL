module TopModule (
    input  logic [5:0] y,
    input  logic w,
    output logic Y1,
    output logic Y3
);

always_comb begin
    Y1 = 1'b0;
    Y3 = 1'b0;
    case (y)
        6'b000001: begin // A
            Y1 = w;
            Y3 = 1'b0;
        end
        6'b000010: begin // B
            Y1 = 1'b0;
            Y3 = ~w;
        end
        6'b000100: begin // C
            Y1 = 1'b0;
            Y3 = ~w;
        end
        6'b001000: begin // D
            Y1 = 1'b0;
            Y3 = 1'b0;
        end
        6'b010000: begin // E
            Y1 = 1'b0;
            Y3 = ~w;
        end
        6'b100000: begin // F
            Y1 = 1'b0;
            Y3 = ~w;
        end
        default: begin
            Y1 = 1'b0;
            Y3 = 1'b0;
        end
    endcase
end

endmodule
