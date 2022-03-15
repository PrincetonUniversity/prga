//# 7 inputs
//# 7 outputs
//# 6 D-type flipflops
//# 41 inverters
//# 118 gates (83 ANDs + 0 NANDs + 35 ORs + 0 NORs)

module s386(clk,v0,v1,v13_D_10,v13_D_11,v13_D_12,v13_D_6,v13_D_7,
  v13_D_8,v13_D_9,v2,v3,v4,v5,v6);
input clk,v6,v5,v4,v3,v2,v1,v0;
output v13_D_12,v13_D_11,v13_D_10,v13_D_9,v13_D_8,v13_D_7,v13_D_6;

  wire v12,v13_D_5,v11,v13_D_4,v10,v13_D_3,v9,v13_D_2,v8,v13_D_1,v7,v13_D_0,
    v3bar,v6bar,v5bar,B35Bbar,B35B,B14Bbar,B14B,B34Bbar,B34B,v4bar,v11bar,
    v8bar,v7bar,v12bar,v0bar,v10bar,v9bar,v1bar,II198,Lv13_D_12,II201,
    Lv13_D_11,II204,Lv13_D_10,II207,Lv13_D_9,II210,Lv13_D_8,II213,Lv13_D_7,
    II216,Lv13_D_6,II219,Lv13_D_5,II222,Lv13_D_4,II225,Lv13_D_3,II228,Lv13_D_2,
    II231,Lv13_D_1,II234,Lv13_D_0,II64,II65,IIII114,IIII113,IIII111,IIII109,
    IIII108,IIII106,IIII105,IIII103,IIII102,IIII100,IIII98,IIII96,II89,IIII94,
    IIII93,IIII91,IIII90,II97,II98,IIII87,II104,IIII85,IIII84,IIII79,IIII77,
    IIII76,IIII74,IIII73,IIII71,IIII69,II124,B40B,IIII66,IIII65,IIII63,IIII62,
    B23B,IIII60,B42B,IIII59,B43B,IIII57,B32B,IIII56,IIII54,IIII53,B27B,IIII51,
    IIII50,B21B,IIII48,IIII47,II148,B38B,IIII44,B29B,IIII43,B30B,IIII41,B17B,
    IIII40,B16B,IIII39,II158,B39B,IIII36,B25B,B26B,IIII35,B28B,II164,B15B,
    II167,B33B,IIII31,B36B,II171,IIII30,II175,IIII28,IIII27,B44B,IIII25,B22B,
    IIII24,B24B,IIII22,B18B,IIII21,B19B,II186,B31B,IIII18,B41B,IIII17,B45B,
    II192,B37B,II195,B20B;

  dff DFF_0(clk,v12,v13_D_5);
  dff DFF_1(clk,v11,v13_D_4);
  dff DFF_2(clk,v10,v13_D_3);
  dff DFF_3(clk,v9,v13_D_2);
  dff DFF_4(clk,v8,v13_D_1);
  dff DFF_5(clk,v7,v13_D_0);
  not NOT_0(v3bar,v3);
  not NOT_1(v6bar,v6);
  not NOT_2(v5bar,v5);
  not NOT_3(B35Bbar,B35B);
  not NOT_4(B14Bbar,B14B);
  not NOT_5(B34Bbar,B34B);
  not NOT_6(v4bar,v4);
  not NOT_7(v11bar,v11);
  not NOT_8(v8bar,v8);
  not NOT_9(v7bar,v7);
  not NOT_10(v12bar,v12);
  not NOT_11(v0bar,v0);
  not NOT_12(v10bar,v10);
  not NOT_13(v9bar,v9);
  not NOT_14(v1bar,v1);
  not NOT_15(II198,Lv13_D_12);
  not NOT_16(v13_D_12,II198);
  not NOT_17(II201,Lv13_D_11);
  not NOT_18(v13_D_11,II201);
  not NOT_19(II204,Lv13_D_10);
  not NOT_20(v13_D_10,II204);
  not NOT_21(II207,Lv13_D_9);
  not NOT_22(v13_D_9,II207);
  not NOT_23(II210,Lv13_D_8);
  not NOT_24(v13_D_8,II210);
  not NOT_25(II213,Lv13_D_7);
  not NOT_26(v13_D_7,II213);
  not NOT_27(II216,Lv13_D_6);
  not NOT_28(v13_D_6,II216);
  not NOT_29(II219,Lv13_D_5);
  not NOT_30(v13_D_5,II219);
  not NOT_31(II222,Lv13_D_4);
  not NOT_32(v13_D_4,II222);
  not NOT_33(II225,Lv13_D_3);
  not NOT_34(v13_D_3,II225);
  not NOT_35(II228,Lv13_D_2);
  not NOT_36(v13_D_2,II228);
  not NOT_37(II231,Lv13_D_1);
  not NOT_38(v13_D_1,II231);
  not NOT_39(II234,Lv13_D_0);
  not NOT_40(v13_D_0,II234);
  and AND4_0(II64,v0bar,v5,v7bar,v8bar);
  and AND4_1(II65,v9,v10,v11bar,v12bar);
  and AND2_0(Lv13_D_12,II64,II65);
  and AND2_1(IIII114,v9bar,v12bar);
  and AND2_2(IIII113,v7bar,v8bar);
  and AND2_3(IIII111,v7bar,v8bar);
  and AND3_0(IIII109,v3bar,v4bar,v11bar);
  and AND2_4(IIII108,v7,v11);
  and AND4_2(IIII106,v5bar,v7bar,v11,v12);
  and AND3_1(IIII105,v2,v11bar,v12bar);
  and AND3_2(IIII103,v8,v11,v12bar);
  and AND3_3(IIII102,v8bar,v11bar,v12);
  and AND2_5(IIII100,v2,v8bar);
  and AND2_6(IIII98,v0,v5);
  and AND2_7(IIII96,v1,v9bar);
  and AND3_4(II89,v5bar,v7bar,v8bar);
  and AND3_5(IIII94,v10,v11bar,II89);
  and AND2_8(IIII93,v9bar,v10bar);
  and AND3_6(IIII91,v0,v11bar,v12bar);
  and AND2_9(IIII90,v9bar,v10bar);
  and AND4_3(II97,v0,v6bar,v7bar,v8bar);
  and AND4_4(II98,v9bar,v10,v11bar,v12bar);
  and AND2_10(Lv13_D_8,II97,II98);
  and AND4_5(IIII87,v5bar,v9,v11bar,v12bar);
  and AND3_7(II104,v2,v3,v8);
  and AND3_8(IIII85,v11bar,v12bar,II104);
  and AND3_9(IIII84,v8bar,v11,v12);
  and AND2_11(IIII79,v11bar,v12bar);
  and AND3_10(IIII77,v0,v8bar,v10);
  and AND4_6(IIII76,v1bar,v4,v10bar,B34Bbar);
  and AND3_11(IIII74,v7,v8bar,v11);
  and AND3_12(IIII73,v4bar,v11bar,B34Bbar);
  and AND3_13(IIII71,v4bar,v11bar,B34Bbar);
  and AND2_12(IIII69,v7,v11bar);
  and AND4_7(II124,B40B,v1,v7bar,v8bar);
  and AND4_8(Lv13_D_10,v9,v11bar,v12bar,II124);
  and AND2_13(IIII66,v4,v7);
  and AND2_14(IIII65,B35B,B34B);
  and AND3_14(IIII63,v9bar,v10bar,v12bar);
  and AND3_15(IIII62,B23B,v7bar,v8bar);
  and AND2_15(IIII60,v1,B42B);
  and AND3_16(IIII59,B43B,v8,v12bar);
  and AND2_16(IIII57,B32B,v7bar);
  and AND3_17(IIII56,v11,v12bar,B14Bbar);
  and AND3_18(IIII54,v0bar,v9bar,v10bar);
  and AND2_17(IIII53,B27B,v1);
  and AND3_19(IIII51,v9bar,v10bar,v12bar);
  and AND3_20(IIII50,B21B,v7bar,v8bar);
  and AND2_18(IIII48,B14B,v11);
  and AND3_21(IIII47,v4bar,v11bar,B34Bbar);
  and AND3_22(II148,B38B,v0,v1bar);
  and AND4_9(Lv13_D_7,v9bar,v10bar,v12bar,II148);
  and AND2_19(IIII44,v8bar,B29B);
  and AND2_20(IIII43,B30B,v12bar);
  and AND3_23(IIII41,v4,v11bar,B17B);
  and AND3_24(IIII40,v3,v8,B16B);
  and AND4_10(IIII39,v5,v7,v8bar,v11);
  and AND3_25(II158,B39B,v7bar,v9bar);
  and AND3_26(Lv13_D_9,v11bar,v12bar,II158);
  and AND4_11(IIII36,v7bar,v8bar,B25B,B26B);
  and AND2_21(IIII35,B28B,v12bar);
  and AND3_27(II164,B15B,v0,v1bar);
  and AND4_12(Lv13_D_0,v9bar,v10bar,v12bar,II164);
  and AND3_28(II167,B33B,v0,v1bar);
  and AND3_29(Lv13_D_5,v9bar,v10bar,II167);
  and AND3_30(IIII31,B36B,v11bar,v12bar);
  and AND3_31(II171,v5,v7bar,v8bar);
  and AND3_32(IIII30,v11,v12,II171);
  and AND3_33(II175,v0,v7bar,v8bar);
  and AND4_13(IIII28,v10,v11bar,v12bar,II175);
  and AND2_22(IIII27,B44B,v10bar);
  and AND2_23(IIII25,v0bar,B22B);
  and AND2_24(IIII24,B24B,v1);
  and AND2_25(IIII22,v7bar,B18B);
  and AND2_26(IIII21,B19B,v12bar);
  and AND3_34(II186,B31B,v0,v1bar);
  and AND3_35(Lv13_D_4,v9bar,v10bar,II186);
  and AND3_36(IIII18,v0bar,v10bar,B41B);
  and AND2_27(IIII17,B45B,v9bar);
  and AND3_37(II192,B37B,v0,v1bar);
  and AND3_38(Lv13_D_6,v9bar,v10bar,II192);
  and AND3_39(II195,B20B,v0,v1bar);
  and AND3_40(Lv13_D_1,v9bar,v10bar,II195);
  or OR2_0(B41B,IIII113,IIII114);
  or OR2_1(B42B,IIII111,v12bar);
  or OR2_2(B43B,IIII108,IIII109);
  or OR2_3(B29B,IIII105,IIII106);
  or OR2_4(B18B,IIII102,IIII103);
  or OR2_5(B17B,v7,IIII100);
  or OR2_6(B40B,IIII98,v10bar);
  or OR2_7(B26B,v0bar,IIII96);
  or OR2_8(B27B,IIII93,IIII94);
  or OR2_9(B23B,IIII90,IIII91);
  or OR2_10(B21B,v10bar,IIII87);
  or OR2_11(B32B,IIII84,IIII85);
  or OR2_12(B34B,v8bar,v3);
  or OR2_13(B14B,v7bar,v8bar);
  or OR2_14(B35B,v2,v7);
  or OR2_15(B25B,v10bar,IIII79);
  or OR2_16(B39B,IIII76,IIII77);
  or OR2_17(B38B,IIII73,IIII74);
  or OR2_18(B30B,IIII71,v7);
  or OR2_19(B16B,B35Bbar,IIII69);
  or OR2_20(B36B,IIII65,IIII66);
  or OR2_21(B24B,IIII62,IIII63);
  or OR2_22(B44B,IIII59,IIII60);
  or OR2_23(B33B,IIII56,IIII57);
  or OR2_24(B28B,IIII53,IIII54);
  or OR2_25(B22B,IIII50,IIII51);
  or OR2_26(B15B,IIII47,IIII48);
  or OR2_27(B31B,IIII43,IIII44);
  or OR3_0(B19B,IIII39,IIII40,IIII41);
  or OR2_28(Lv13_D_3,IIII35,IIII36);
  or OR2_29(B37B,IIII30,IIII31);
  or OR2_30(B45B,IIII27,IIII28);
  or OR2_31(Lv13_D_2,IIII24,IIII25);
  or OR2_32(B20B,IIII21,IIII22);
  or OR2_33(Lv13_D_11,IIII17,IIII18);

endmodule
