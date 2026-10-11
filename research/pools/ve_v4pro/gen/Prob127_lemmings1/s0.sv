module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);
    localparam LEFT  = 1'b0;
    localparam RIGHT = 1'b1;

    logic state;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= LEFT;
        end else begin
            case (state)
                LEFT:  state <= bump_left ? RIGHT : LEFT;
                RIGHT: state <= bump_right ? LEFT : RIGHT;
                default: state <= LEFT;
            endcase
        end
    end

    assign walk_left  = (state == LEFT);
    assign walk_right = (state == RIGHT);
endmodule
