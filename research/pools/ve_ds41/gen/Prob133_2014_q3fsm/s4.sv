module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic s,
    input  logic w,
    output logic z
);

    typedef enum logic [2:0] {
        A    = 3'd0,
        S1_0 = 3'd1,
        S1_1 = 3'd2,
        S2_0 = 3'd3,
        S2_1 = 3'd4,
        S3_0 = 3'd5,
        S3_1 = 3'd6,
        S3_2 = 3'd7
    } state_t;

    state_t state, next;

    always_ff @(posedge clk) begin
        if (reset) state <= A;
        else       state <= next;
    end

    always_comb begin
        case (state)
            A:    next = s ? S1_0 : A;
            S1_0: next = w ? S2_1 : S2_0;
            S1_1: next = w ? S2_1 : S2_0;
            S2_0: next = w ? S3_1 : S3_0;
            S2_1: next = w ? S3_2 : S3_1;
            S3_0: next = S1_0;
            S3_1: next = w ? S1_1 : S1_0;
            S3_2: next = w ? S1_0 : S1_1;
            default: next = A;
        endcase
    end

    assign z = (state == S1_1);

endmodule
