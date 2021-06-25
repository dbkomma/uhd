module freq_shift_dk #(
  parameter DATA_WIDTH = 16,
  parameter DDS_WIDTH  = 24,
  parameter SIN_COS_WIDTH = 16,
  parameter PHASE_WIDTH = 24, 
  parameter SCALING_WIDTH = 18
)(
  input   clk,
  input   reset,

  /* IQ input */
  input [DATA_WIDTH-1:0]  iin,
  input [DATA_WIDTH-1:0]  qin,
  input in_tvalid,
  input in_tlast, 
  output in_tready,

  
  /* phase increment */
  input [PHASE_WIDTH-1:0]  phase_inc,
  input phase_tvalid,
  input phase_tlast, 
  output phase_tready,

  /* IQ output */
  output [DATA_WIDTH-1:0]  iout,
  output [DATA_WIDTH-1:0]  qout,
  output  out_tlast,
  output  out_tvalid,
  input   out_tready,

  /* debug signals */
  output [SIN_COS_WIDTH-1:0]  sin,
  output [SIN_COS_WIDTH-1:0]  cos
);


reg  [PHASE_WIDTH-1:0] phase;
wire [PHASE_WIDTH-1:0] phase_tdata = phase;
/*
wire phase_tvalid = 1'b1;
wire phase_tready;
wire phase_tlast = 1'b0;
*/

wire [DDS_WIDTH-1:0] fshift_in_q_tdata, fshift_in_i_tdata;
wire [2*DDS_WIDTH-1:0] fshift_in_tdata = {fshift_in_q_tdata, fshift_in_i_tdata};
wire [2*DDS_WIDTH-1:0] fshift_out_tdata;
wire [DDS_WIDTH-1:0] fshift_out_q_tdata = fshift_out_tdata[2*DDS_WIDTH-1:DDS_WIDTH];
wire [DDS_WIDTH-1:0] fshift_out_i_tdata = fshift_out_tdata[DDS_WIDTH-1:0];

wire fshift_in_tvalid = in_tvalid;
wire fshift_in_tlast  = in_tlast;
wire fshift_in_tready, fshift_out_tlast, fshift_out_tvalid;
assign in_tready = fshift_in_tready;

wire [2*DATA_WIDTH-1:0] out_tdata; 
assign iout = out_tdata[2*DATA_WIDTH-1:DATA_WIDTH];
assign qout = out_tdata[DATA_WIDTH-1:0];

wire [2*SIN_COS_WIDTH-1:0] sin_cos_data;
assign sin = sin_cos_data[2*SIN_COS_WIDTH-1:SIN_COS_WIDTH];
assign cos = sin_cos_data[SIN_COS_WIDTH-1:0];


sign_extend #(.bits_in(DATA_WIDTH), 
              .bits_out(DDS_WIDTH))
    sign_extend_fshift_i (
        .in(iin), 
        .out(fshift_in_i_tdata));

sign_extend #(.bits_in(DATA_WIDTH), 
              .bits_out(DDS_WIDTH))
    sign_extend_fshift_q (
        .in(qin), 
        .out(fshift_in_q_tdata));


dds_freq_tune #(.OUTPUT_WIDTH(DDS_WIDTH))
    dds_freq_tune_inst (
    .clk(clk),
    .reset(reset),
    .eob(1'b0),
    .rate_changed(1'b0),

    /* IQ input */
    .s_axis_din_tlast(fshift_in_tlast),
    .s_axis_din_tvalid(fshift_in_tvalid),
    .s_axis_din_tready(fshift_in_tready),
    .s_axis_din_tdata(fshift_in_tdata),

    /* Phase input from NCO */
    .s_axis_phase_tlast(phase_tlast),
    .s_axis_phase_tvalid(phase_tvalid),
    .s_axis_phase_tready(phase_tready),
    .s_axis_phase_tdata(phase_tdata), //24 bit

    /* IQ output */
    .m_axis_dout_tlast(fshift_out_tlast), 
    .m_axis_dout_tvalid(fshift_out_tvalid), 
    .m_axis_dout_tready(1'b1),
    .m_axis_dout_tdata(fshift_out_tdata),

    /*debug*/
    .m_axis_dds_tdata_out(sin_cos_data)
);

  /************************************************************************
  * Perform scaling on the IQ output
  ************************************************************************/
    wire [DDS_WIDTH+SCALING_WIDTH-1:0] scaled_i_tdata, scaled_q_tdata;
    wire scaled_tlast, scaled_tvalid, scaled_tready;
    wire [SCALING_WIDTH-1:0] scaling_tdata = 1 << 15;

  mult #(
   .WIDTH_A(DDS_WIDTH),
   .WIDTH_B(SCALING_WIDTH),
   .WIDTH_P(DDS_WIDTH+SCALING_WIDTH),
   .DROP_TOP_P(4),
   .LATENCY(3),
   .CASCADE_OUT(0))
  i_mult (
    .clk(clk), .reset(reset),
    .a_tdata(fshift_out_i_tdata), .a_tlast(fshift_out_tlast), 
    .a_tvalid(fshift_out_tvalid), .a_tready(),
    .b_tdata(scaling_tdata), .b_tlast(1'b0), 
    .b_tvalid(fshift_out_tvalid), .b_tready(),
    .p_tdata(scaled_i_tdata), .p_tlast(scaled_tlast), 
    .p_tvalid(scaled_tvalid), .p_tready(scaled_tready));

  mult #(
   .WIDTH_A(DDS_WIDTH),
   .WIDTH_B(SCALING_WIDTH),
   .WIDTH_P(DDS_WIDTH+SCALING_WIDTH),
   .DROP_TOP_P(4),
   .LATENCY(3),
   .CASCADE_OUT(0))
  q_mult (
    .clk(clk), .reset(reset),
    .a_tdata(fshift_out_q_tdata), .a_tlast(), 
    .a_tvalid(fshift_out_tvalid), .a_tready(),
    .b_tdata(scaling_tdata), .b_tlast(1'b0), 
    .b_tvalid(fshift_out_tvalid), .b_tready(),
    .p_tdata(scaled_q_tdata), .p_tlast(), 
    .p_tvalid(), .p_tready(scaled_tready));

 
  wire sample_tlast, sample_tvalid, sample_tready;

    axi_round_and_clip_complex #(.WIDTH_IN(DDS_WIDTH+SCALING_WIDTH), 
                                 .WIDTH_OUT(DATA_WIDTH), 
                                 .CLIP_BITS(12))
        axi_round_and_clip_complex (
          .clk(clk), .reset(reset ),
          .i_tdata({scaled_i_tdata, scaled_q_tdata}), 
          .i_tlast(scaled_tlast), .i_tvalid(scaled_tvalid), .i_tready(scaled_tready),
          .o_tdata(out_tdata), .o_tlast(out_tlast), 
          .o_tvalid(out_tvalid), .o_tready(out_tready));


always @(posedge clk) begin
    if (reset) begin
      phase <= 0;

    end 
    else  begin 
      phase <= phase + phase_inc;
    end
end

endmodule