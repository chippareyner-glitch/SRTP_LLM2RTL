module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    // ------------------------------------------------------------------
    // Decode the sensor pattern into the current water level.
    //   s[2] : highest sensor   (level 3 : above s[2])
    //   s[1] : middle  sensor   (level 2 : between s[2] and s[1])
    //   s[0] : lowest  sensor   (level 1 : between s[1] and s[0])
    //                           (level 0 : below s[0])
    // ------------------------------------------------------------------
    logic [1:0] cur_lev;
    always_comb begin
        if      (s[2]) cur_lev = 2'd3;
        else if (s[1]) cur_lev = 2'd2;
        else if (s[0]) cur_lev = 2'd1;
        else           cur_lev = 2'd0;
    end

    // ------------------------------------------------------------------
    // State = the level prior to the last sensor change.
    // Active-high synchronous reset -> state "low for a long time".
    // ------------------------------------------------------------------
    logic [1:0] prev_lev;
    always_ff @(posedge clk) begin
        if (reset) prev_lev <= 2'd0;
        else       prev_lev <= cur_lev;
    end

    // ------------------------------------------------------------------
    // Mealy outputs : combinational, respond to s in the same cycle
    // ------------------------------------------------------------------
    // Nominal flow valves (thermometer coded)
    assign fr0 = (cur_lev != 2'd3);                        // asserted for levels 2,1,0
    assign fr1 = (cur_lev == 2'd1) || (cur_lev == 2'd0);   // asserted for levels 1,0
    assign fr2 = (cur_lev == 2'd0);                        // asserted for level 0

    // Supplemental flow valve:
    //  - below the lowest sensor      -> always open (maximum flow)
    //  - between the sensors          -> open only if the previous level
    //                                    was lower than the current level
    //  - above the highest sensor     -> flow rate must be zero
    assign dfr = (cur_lev == 2'd0) ||
                 ((cur_lev != 2'd3) && (prev_lev < cur_lev));

endmodule
