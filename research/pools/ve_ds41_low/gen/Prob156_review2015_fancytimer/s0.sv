module TopModule (
    input  clk,
    input  reset,
    input  data,
    output [3:0] count,
    output       counting,
    output       done,
    input        ack
);

    localparam SEARCH = 2'd0,
               SHIFT  = 2'd1,
               COUNT  = 2'd2,
               DONE   = 2'd3;

    reg [1:0] state, next_state;
    reg [3:0] sr;         // pattern-detection shift register
    reg [3:0] delay;      // captured delay value
    reg [3:0] count_val;  // current remaining-time value
    reg [9:0] sub;        // 0..999 cycle sub-counter
    reg [1:0] bitcnt;     // counts the 4 delay bits

    wire [3:0] sr_next    = {sr[2:0], data};
    wire [3:0] delay_next = {delay[2:0], data};

    // ---------- next-state logic ----------
    always @(*) begin
        next_state = state;
        case (state)
            SEARCH: if (sr_next == 4'b1101)                 next_state = SHIFT;
            SHIFT : if (bitcnt == 2'd3)                     next_state = COUNT;
            COUNT : if (sub == 10'd999 && count_val == 4'd0) next_state = DONE;
            DONE  : if (ack)                                next_state = SEARCH;
            default: next_state = SEARCH;
        endcase
    end

    // ---------- sequential logic ----------
    always @(posedge clk) begin
        if (reset) begin
            state     <= SEARCH;
            sr        <= 4'd0;
            delay     <= 4'd0;
            count_val <= 4'd0;
            sub       <= 10'd0;
            bitcnt    <= 2'd0;
        end
        else begin
            state <= next_state;
            case (state)
                SEARCH: begin
                    sr <= sr_next;
                end

                SHIFT: begin
                    delay  <= delay_next;
                    bitcnt <= (bitcnt == 2'd3) ? 2'd0 : (bitcnt + 2'd1);
                    if (bitcnt == 2'd3)
                        count_val <= delay_next;
                end

                COUNT: begin
                    if (sub == 10'd999) begin
                        sub <= 10'd0;
                        if (count_val != 4'd0)
                            count_val <= count_val - 4'd1;
                    end
                    else begin
                        sub <= sub + 10'd1;
                    end
                end

                DONE: begin
                    if (ack)
                        sr <= 4'd0;   // start the next search cleanly
                end
            endcase
        end
    end

    // ---------- outputs ----------
    assign count    = count_val;
    assign counting = (state == COUNT);
    assign done     = (state == DONE);

endmodule
