module TopModule (
    input  [15:0] scancode,
    output logic left,
    output logic down,
    output logic right,
    output logic up
);

    always_comb begin
        left  = (scancode == 16'hE06B);
        down  = (scancode == 16'hE072);
        right = (scancode == 16'hE074);
        up    = (scancode == 16'hE075);
    end

endmodule
