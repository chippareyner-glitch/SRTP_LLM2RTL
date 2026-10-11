module calendar (
    input  logic       CLK,
    input  logic       RST,
    output logic [5:0] Hours,
    output logic [5:0] Mins,
    output logic [5:0] Secs
);

    always @(posedge CLK or posedge RST) begin
        if (RST)
            Secs <= 6'd0;
        else if (Secs == 6'd59)
            Secs <= 6'd0;
        else
            Secs <= Secs + 6'd1;
    end

    always @(posedge CLK or posedge RST) begin
        if (RST)
            Mins <= 6'd0;
        else if (Mins == 6'd59 && Secs == 6'd59)
            Mins <= 6'd0;
        else if (Secs == 6'd59)
            Mins <= Mins + 6'd1;
        else
            Mins <= Mins;
    end

    always @(posedge CLK or posedge RST) begin
        if (RST)
            Hours <= 6'd0;
        else if (Hours == 6'd23 && Mins == 6'd59 && Secs == 6'd59)
            Hours <= 6'd0;
        else if (Mins == 6'd59 && Secs == 6'd59)
            Hours <= Hours + 6'd1;
        else
            Hours <= Hours;
    end

endmodule
