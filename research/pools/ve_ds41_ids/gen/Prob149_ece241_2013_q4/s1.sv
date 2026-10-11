module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    typedef enum logic [2:0] {
        LOW,
        L1_UP,
        L1_DOWN,
        L2_UP,
        L2_DOWN,
        HIGH
    } state_t;

    state_t state, next_state;
    logic [1:0] curr_level, new_level;

    always_comb begin
        case (state)
            LOW:            curr_level = 2'd0;
            L1_UP, L1_DOWN: curr_level = 2'd1;
            L2_UP, L2_DOWN: curr_level = 2'd2;
            HIGH:           curr_level = 2'd3;
            default:        curr_level = 2'd0;
        endcase
    end

    always_comb begin
        case (s)
            3'b000: new_level = 2'd0;
            3'b001: new_level = 2'd1;
            3'b011: new_level = 2'd2;
            3'b111: new_level = 2'd3;
            default: new_level = curr_level;
        endcase
    end

    always_comb begin
        if (new_level > curr_level) begin
            case (new_level)
                2'd0: next_state = LOW;
                2'd1: next_state = L1_UP;
                2'd2: next_state = L2_UP;
                2'd3: next_state = HIGH;
                default: next_state = state;
            endcase
        end else if (new_level < curr_level) begin
            case (new_level)
                2'd0: next_state = LOW;
                2'd1: next_state = L1_DOWN;
                2'd2: next_state = L2_DOWN;
                2'd3: next_state = HIGH;
                default: next_state = state;
            endcase
        end else begin
            next_state = state;
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= LOW;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        case (state)
            LOW: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
                dfr = 1'b1;
            end
            L1_UP: begin
                fr2 = 1'b0;
                fr1 = 1'b1;
                fr0 = 1'b1;
                dfr = 1'b1;
            end
            L1_DOWN: begin
                fr2 = 1'b0;
                fr1 = 1'b1;
                fr0 = 1'b1;
                dfr = 1'b0;
            end
            L2_UP: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b1;
                dfr = 1'b1;
            end
            L2_DOWN: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b1;
                dfr = 1'b0;
            end
            HIGH: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
                dfr = 1'b0;
            end
            default: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
                dfr = 1'b0;
            end
        endcase
    end

endmodule
