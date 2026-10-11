module TopModule (
    input  logic clk,
    input  logic resetn,
    input  logic x,
    input  logic y,
    output logic f,
    output logic g
);

    // State encoding
    typedef enum logic [3:0] {
        A    = 4'd0,  // beginning / reset state
        FST  = 4'd1,  // f = 1 for one cycle
        S0   = 4'd2,  // looking for first x = 1
        S1   = 4'd3,  // have 1, looking for 0
        S2   = 4'd4,  // have 1,0, looking for 1
        G1   = 4'd5,  // g = 1, first y-monitor cycle (T)
        G2   = 4'd6,  // g = 1, second y-monitor cycle (T+1)
        GON  = 4'd7,  // g = 1 permanently
        GOFF = 4'd8   // g = 0 permanently
    } state_t;

    state_t state, next;

    // Sequential logic: synchronous, active-low reset
    always_ff @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next;
    end

    // Next-state logic
    always_comb begin
        next = state;
        case (state)
            A:    next = FST;              // reset de-asserted -> assert f next cycle
            FST:  next = S0;               // f high for exactly one cycle, then monitor x
            S0:   next = x ? S1 : S0;      // wait for x = 1
            S1:   next = x ? S1 : S2;      // wait for x = 0
            S2:   next = x ? G1 : S0;      // wait for x = 1 -> sequence 1,0,1 found
            G1:   next = y ? GON : G2;     // cycle T   : check y
            G2:   next = y ? GON : GOFF;   // cycle T+1 : check y
            GON:  next = GON;              // latch g = 1 permanently
            GOFF: next = GOFF;             // latch g = 0 permanently
            default: next = A;
        endcase
    end

    // Moore outputs
    assign f = (state == FST);
    assign g = (state == G1) || (state == G2) || (state == GON);

endmodule
