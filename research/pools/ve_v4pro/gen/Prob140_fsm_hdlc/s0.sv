module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic in,
    output logic disc,
    output logic flag,
    output logic err
);

    typedef enum logic [3:0] {
        IDLE = 4'd0,
        ONE1 = 4'd1,
        ONE2 = 4'd2,
        ONE3 = 4'd3,
        ONE4 = 4'd4,
        ONE5 = 4'd5,
        ONE6 = 4'd6,
        DISC = 4'd7,
        FLAG = 4'd8,
        ERR  = 4'd9
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk) begin
        if (reset)
            state <= IDLE;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE:  next_state = in ? ONE1 : IDLE;
            ONE1:  next_state = in ? ONE2 : IDLE;
            ONE2:  next_state = in ? ONE3 : IDLE;
            ONE3:  next_state = in ? ONE4 : IDLE;
            ONE4:  next_state = in ? ONE5 : IDLE;
            ONE5:  next_state = in ? ONE6 : DISC;
            ONE6:  next_state = in ? ERR  : FLAG;
            DISC:  next_state = in ? ONE1 : IDLE;
            FLAG:  next_state = in ? ONE1 : IDLE;
            ERR:   next_state = in ? ERR  : IDLE;
            default: next_state = IDLE;
        endcase
    end

    assign disc = (state == DISC);
    assign flag = (state == FLAG);
    assign err  = (state == ERR);

endmodule
