module TopModule (
    input  a,
    input  b,
    input  sel_b1,
    input  sel_b2,
    output wire  out_assign,
    output logic out_always
);

    assign out_assign = (sel_b1 && sel_b2) ? b : a;

    always_comb begin
        if (sel_b1 && sel_b2)
            out_always = b;
        else
            out_always = a;
    end

endmodule
