// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vsoc_b.h for the primary calling header

#include "Vsoc_b__pch.h"

void Vsoc_b___024root___eval_sample(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_sample\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__ico(const ::VlUnpacked<::QData/*63:0*/, 2> &triggers, const ::std::string &tag);
#endif  // VL_DEBUG

bool Vsoc_b___024root___eval_ico(Vsoc_b___024root* vlSelf, ::CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_ico\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VicoTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VicoTriggered[1U]) 
                                     | (::IData)((::IData)(firstIteration)));
    {
        // Inlined CFunc: _eval_triggers_vec__ico
        vlSelfRef.__VicoTriggered[0U] = (::QData)((::IData)(
                                                            ((((::IData)(vlSelfRef.__VprimaryPorts.uart_rx) 
                                                               != (::IData)(vlSelfRef.__Vtrigprevexpr___TOP__uart_rx__0)) 
                                                              << 2U) 
                                                             | ((((::IData)(vlSelfRef.__VprimaryPorts.resetn) 
                                                                  != (::IData)(vlSelfRef.__Vtrigprevexpr___TOP__resetn__0)) 
                                                                 << 1U) 
                                                                | ((::IData)(vlSelfRef.__VprimaryPorts.clk) 
                                                                   != (::IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__0))))));
        vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.__VprimaryPorts.clk;
        vlSelfRef.__Vtrigprevexpr___TOP__resetn__0 
            = vlSelfRef.__VprimaryPorts.resetn;
        vlSelfRef.__Vtrigprevexpr___TOP__uart_rx__0 
            = vlSelfRef.__VprimaryPorts.uart_rx;
        if (VL_UNLIKELY(((1U & (~ (::IData)(vlSelfRef.__VicoDidInit)))))) {
            vlSelfRef.__VicoDidInit = 1U;
            vlSelfRef.__VicoTriggered[0U] = (1ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (2ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (4ULL | vlSelfRef.__VicoTriggered[0U]);
        }
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vsoc_b___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    return (0U);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__act(const ::VlUnpacked<::QData/*63:0*/, 1> &triggers, const ::std::string &tag);
#endif  // VL_DEBUG
void Vsoc_b___024root___trigger_orInto__act_vec_vec(::VlUnpacked<::QData/*63:0*/, 1> &out, const ::VlUnpacked<::QData/*63:0*/, 1> &in);

bool Vsoc_b___024root___eval_act(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_act\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__act
        vlSelfRef.__VactTriggered[0U] = (::QData)((::IData)(
                                                            ((::IData)(vlSelfRef.__VprimaryPorts.clk) 
                                                             & (~ (::IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__1)))));
        vlSelfRef.__Vtrigprevexpr___TOP__clk__1 = vlSelfRef.__VprimaryPorts.clk;
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vsoc_b___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vsoc_b___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

bool Vsoc_b___024root___eval_inact(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_inact\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vsoc_b___024root___trigger_anySet__act(const ::VlUnpacked<::QData/*63:0*/, 1> &in);
void Vsoc_b___024root___nba_sequent__TOP__0(Vsoc_b___024root* vlSelf);
void Vsoc_b___024root___trigger_clear__act(::VlUnpacked<::QData/*63:0*/, 1> &out);

bool Vsoc_b___024root___eval_nba(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_nba\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    ::CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vsoc_b___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        {
            // Inlined CFunc: _eval_body__nba
            if ((((1ULL & vlSelfRef.__VnbaTriggered[0U])) != 0ULL)) {
                Vsoc_b___024root___nba_sequent__TOP__0(vlSelf);
            }
        }
        Vsoc_b___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

bool Vsoc_b___024root___eval_obs(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_obs\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vsoc_b___024root___eval_react(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_react\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

void Vsoc_b___024root___eval_postponed(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_postponed\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

bool Vsoc_b___024root___trigger_anySet__ico(const ::VlUnpacked<::QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___trigger_anySet__ico\n"); );
    // Locals
    ::IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((::IData)(1U) + n);
    } while ((2U > n));
    return (0U);
}

bool Vsoc_b___024root___trigger_anySet__act(const ::VlUnpacked<::QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___trigger_anySet__act\n"); );
    // Locals
    ::IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((::IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void Vsoc_b___024root___nba_sequent__TOP__0(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___nba_sequent__TOP__0\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__imm_i;
    soc_b__DOT__u_core__DOT__imm_i = 0;
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__alu_b;
    soc_b__DOT__u_core__DOT__alu_b = 0;
    ::CData/*4:0*/ soc_b__DOT__u_core__DOT__shamt;
    soc_b__DOT__u_core__DOT__shamt = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__lt_s;
    soc_b__DOT__u_core__DOT__lt_s = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__lt_u;
    soc_b__DOT__u_core__DOT__lt_u = 0;
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__ld_addr;
    soc_b__DOT__u_core__DOT__ld_addr = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__is_csr;
    soc_b__DOT__u_core__DOT__is_csr = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_717;
    __Vdfg_Regularize_717 = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_718;
    __Vdfg_Regularize_718 = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_719;
    __Vdfg_Regularize_719 = 0;
    ::IData/*31:0*/ __Vdly__soc_b__DOT__hw_cnt_5;
    __Vdly__soc_b__DOT__hw_cnt_5 = 0;
    ::CData/*1:0*/ __Vdly__soc_b__DOT__u_rx__DOT__st_16;
    __Vdly__soc_b__DOT__u_rx__DOT__st_16 = 0;
    ::SData/*8:0*/ __Vdly__soc_b__DOT__u_rx__DOT__c_17;
    __Vdly__soc_b__DOT__u_rx__DOT__c_17 = 0;
    ::CData/*7:0*/ __Vdly__soc_b__DOT__u_rx__DOT__sh_18;
    __Vdly__soc_b__DOT__u_rx__DOT__sh_18 = 0;
    ::SData/*9:0*/ __Vdly__soc_b__DOT__u_tx__DOT__sh_20;
    __Vdly__soc_b__DOT__u_tx__DOT__sh_20 = 0;
    ::CData/*3:0*/ __Vdly__soc_b__DOT__u_tx__DOT__n_21;
    __Vdly__soc_b__DOT__u_tx__DOT__n_21 = 0;
    ::CData/*7:0*/ __Vdly__soc_b__DOT__u_tx__DOT__c_22;
    __Vdly__soc_b__DOT__u_tx__DOT__c_22 = 0;
    ::QData/*63:0*/ __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23;
    __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23 = 0;
    ::CData/*2:0*/ __Vdly__soc_b__DOT__u_core__DOT__state_24;
    __Vdly__soc_b__DOT__u_core__DOT__state_24 = 0;
    ::IData/*31:0*/ __Vdly__soc_b__DOT__u_core__DOT__quo_28;
    __Vdly__soc_b__DOT__u_core__DOT__quo_28 = 0;
    ::CData/*5:0*/ __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29;
    __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = 0;
    ::QData/*63:0*/ __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31;
    __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 = 0;
    ::CData/*0:0*/ __Vdly__dbg_trap_35;
    __Vdly__dbg_trap_35 = 0;
    ::CData/*7:0*/ __Vdly_Val__soc_b__DOT__ram_49;
    __Vdly_Val__soc_b__DOT__ram_49 = 0;
    ::SData/*13:0*/ __Vdly_Dim0__soc_b__DOT__ram_50;
    __Vdly_Dim0__soc_b__DOT__ram_50 = 0;
    ::CData/*0:0*/ __Vdly_Set__soc_b__DOT__ram_51;
    __Vdly_Set__soc_b__DOT__ram_51 = 0;
    ::CData/*7:0*/ __Vdly_Val__soc_b__DOT__ram_52;
    __Vdly_Val__soc_b__DOT__ram_52 = 0;
    ::SData/*13:0*/ __Vdly_Dim0__soc_b__DOT__ram_53;
    __Vdly_Dim0__soc_b__DOT__ram_53 = 0;
    ::CData/*0:0*/ __Vdly_Set__soc_b__DOT__ram_54;
    __Vdly_Set__soc_b__DOT__ram_54 = 0;
    ::CData/*7:0*/ __Vdly_Val__soc_b__DOT__ram_55;
    __Vdly_Val__soc_b__DOT__ram_55 = 0;
    ::SData/*13:0*/ __Vdly_Dim0__soc_b__DOT__ram_56;
    __Vdly_Dim0__soc_b__DOT__ram_56 = 0;
    ::CData/*0:0*/ __Vdly_Set__soc_b__DOT__ram_57;
    __Vdly_Set__soc_b__DOT__ram_57 = 0;
    ::CData/*7:0*/ __Vdly_Val__soc_b__DOT__ram_58;
    __Vdly_Val__soc_b__DOT__ram_58 = 0;
    ::SData/*13:0*/ __Vdly_Dim0__soc_b__DOT__ram_59;
    __Vdly_Dim0__soc_b__DOT__ram_59 = 0;
    ::CData/*0:0*/ __Vdly_Set__soc_b__DOT__ram_60;
    __Vdly_Set__soc_b__DOT__ram_60 = 0;
    ::IData/*31:0*/ __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61;
    __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61 = 0;
    ::CData/*4:0*/ __Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62;
    __Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62 = 0;
    ::CData/*0:0*/ __Vdly_Set__soc_b__DOT__u_core__DOT__regs_63;
    __Vdly_Set__soc_b__DOT__u_core__DOT__regs_63 = 0;
    // Body
    __Vdly__soc_b__DOT__u_rx__DOT__c_17 = vlSelfRef.soc_b__DOT__u_rx__DOT__c;
    __Vdly__soc_b__DOT__u_rx__DOT__st_16 = vlSelfRef.soc_b__DOT__u_rx__DOT__st;
    __Vdly__soc_b__DOT__u_rx__DOT__sh_18 = vlSelfRef.soc_b__DOT__u_rx__DOT__sh;
    __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23 = vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle;
    __Vdly__dbg_trap_35 = vlSelfRef.__VprimaryPorts.dbg_trap;
    __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 
        = vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret;
    __Vdly__soc_b__DOT__u_core__DOT__state_24 = vlSelfRef.soc_b__DOT__u_core__DOT__state;
    __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt;
    __Vdly__soc_b__DOT__u_tx__DOT__n_21 = vlSelfRef.soc_b__DOT__u_tx__DOT__n;
    __Vdly__soc_b__DOT__u_tx__DOT__c_22 = vlSelfRef.soc_b__DOT__u_tx__DOT__c;
    __Vdly__soc_b__DOT__u_core__DOT__quo_28 = vlSelfRef.soc_b__DOT__u_core__DOT__quo;
    __Vdly_Set__soc_b__DOT__ram_51 = 0U;
    __Vdly_Set__soc_b__DOT__ram_54 = 0U;
    __Vdly_Set__soc_b__DOT__ram_57 = 0U;
    __Vdly_Set__soc_b__DOT__ram_60 = 0U;
    __Vdly__soc_b__DOT__u_tx__DOT__sh_20 = vlSelfRef.soc_b__DOT__u_tx__DOT__sh;
    __Vdly__soc_b__DOT__hw_cnt_5 = vlSelfRef.soc_b__DOT__hw_cnt;
    __Vdly_Set__soc_b__DOT__u_core__DOT__regs_63 = 0U;
    if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__n))) {
        if (vlSelfRef.soc_b__DOT__tx_start) {
            __Vdly__soc_b__DOT__u_tx__DOT__n_21 = 0x0aU;
            __Vdly__soc_b__DOT__u_tx__DOT__c_22 = 0xe9U;
            __Vdly__soc_b__DOT__u_tx__DOT__sh_20 = 
                (0x00000200U | ((::IData)(vlSelfRef.soc_b__DOT__tx_byte) 
                                << 1U));
        }
    } else if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__c))) {
        __Vdly__soc_b__DOT__u_tx__DOT__n_21 = (0x0000000fU 
                                               & ((::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__n) 
                                                  - (::IData)(1U)));
        __Vdly__soc_b__DOT__u_tx__DOT__c_22 = 0x000000e9U;
        __Vdly__soc_b__DOT__u_tx__DOT__sh_20 = (0x00000200U 
                                                | (0x000001ffU 
                                                   & ((::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__sh) 
                                                      >> 1U)));
    } else {
        __Vdly__soc_b__DOT__u_tx__DOT__c_22 = (0x000000ffU 
                                               & ((::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__c) 
                                                  - (::IData)(1U)));
    }
    if ((((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid) 
          & (0U == (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                    >> 0x0000001cU))) & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r)))) {
        if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r))) {
            __Vdly_Val__soc_b__DOT__ram_49 = (0x000000ffU 
                                              & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r);
            __Vdly_Dim0__soc_b__DOT__ram_50 = (0x00003fffU 
                                               & (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                                  >> 2U));
            __Vdly_Set__soc_b__DOT__ram_51 = 1U;
        }
        if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r))) {
            __Vdly_Val__soc_b__DOT__ram_52 = (0x000000ffU 
                                              & (vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r 
                                                 >> 8U));
            __Vdly_Dim0__soc_b__DOT__ram_53 = (0x00003fffU 
                                               & (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                                  >> 2U));
            __Vdly_Set__soc_b__DOT__ram_54 = 1U;
        }
        if ((4U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r))) {
            __Vdly_Val__soc_b__DOT__ram_55 = (0x000000ffU 
                                              & (vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r 
                                                 >> 0x10U));
            __Vdly_Dim0__soc_b__DOT__ram_56 = (0x00003fffU 
                                               & (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                                  >> 2U));
            __Vdly_Set__soc_b__DOT__ram_57 = 1U;
        }
        if ((8U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r))) {
            __Vdly_Val__soc_b__DOT__ram_58 = (vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r 
                                              >> 0x18U);
            __Vdly_Dim0__soc_b__DOT__ram_59 = (0x00003fffU 
                                               & (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                                  >> 2U));
            __Vdly_Set__soc_b__DOT__ram_60 = 1U;
        }
    }
    if (vlSelfRef.soc_b__DOT__hw_run) {
        __Vdly__soc_b__DOT__hw_cnt_5 = ((::IData)(1U) 
                                        + vlSelfRef.soc_b__DOT__hw_cnt);
    }
    if (((::IData)(vlSelfRef.__VprimaryPorts.resetn) 
         & ((1U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))
             ? (::IData)(vlSelfRef.__Vdfg_Regularize_712)
             : ((2U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))
                 ? (::IData)(vlSelfRef.__Vdfg_Regularize_710)
                 : (::IData)(vlSelfRef.__Vdfg_Regularize_711))))) {
        if ((1U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
            __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61 
                = (((0x00000040U & vlSelfRef.soc_b__DOT__mem_rdata)
                     ? (((0x00000010U & vlSelfRef.soc_b__DOT__mem_rdata)
                          ? (((0x0c00U == (vlSelfRef.soc_b__DOT__mem_rdata 
                                           >> 0x00000014U))
                               ? (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle)
                               : ((0x0c80U == (vlSelfRef.soc_b__DOT__mem_rdata 
                                               >> 0x00000014U))
                                   ? (::IData)((vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle 
                                                >> 0x00000020U))
                                   : ((0x0c02U == (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x00000014U))
                                       ? (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret)
                                       : ((::IData)(
                                                    (vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret 
                                                     >> 0x00000020U)) 
                                          & (- (::IData)(
                                                         (0x0c82U 
                                                          == 
                                                          (vlSelfRef.soc_b__DOT__mem_rdata 
                                                           >> 0x00000014U)))))))) 
                             & (- (::IData)(((~ (vlSelfRef.soc_b__DOT__mem_rdata 
                                                 >> 2U)) 
                                             & (::IData)(vlSelfRef.__Vdfg_Regularize_716)))))
                          : (((::IData)(4U) + vlSelfRef.soc_b__DOT__u_core__DOT__pc) 
                             & (- (::IData)((7U == 
                                             (7U & vlSelfRef.soc_b__DOT__mem_rdata)))))) 
                        & (- (::IData)((1U & (vlSelfRef.soc_b__DOT__mem_rdata 
                                              >> 5U)))))
                     : ((0x00000020U & vlSelfRef.soc_b__DOT__mem_rdata)
                         ? ((- (::IData)((1U & (~ (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 3U))))) 
                            & (((4U & vlSelfRef.soc_b__DOT__mem_rdata)
                                 ? (0xfffff000U & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   & (- (::IData)(
                                                                  (3U 
                                                                   == 
                                                                   (3U 
                                                                    & vlSelfRef.soc_b__DOT__mem_rdata))))))
                                 : vlSelfRef.__Vdfg_Regularize_715) 
                               & (- (::IData)((1U & 
                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                >> 4U))))))
                         : ((- (::IData)((1U & (~ (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 3U))))) 
                            & (((4U & vlSelfRef.soc_b__DOT__mem_rdata)
                                 ? ((vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                     + (0xfffff000U 
                                        & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                    & (- (::IData)(
                                                   (3U 
                                                    == 
                                                    (3U 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)))))
                                 : vlSelfRef.__Vdfg_Regularize_715) 
                               & (- (::IData)((1U & 
                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                >> 4U)))))))) 
                   & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_712))));
            __Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62 
                = (0x0000001fU & ((vlSelfRef.soc_b__DOT__mem_rdata 
                                   >> 7U) & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_712)))));
        } else if ((2U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
            __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61 
                = (((4U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3))
                     ? ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3))
                         ? vlSelfRef.soc_b__DOT__mem_rdata
                         : ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3))
                             ? (::IData)(vlSelfRef.__Vdfg_Regularize_707)
                             : (::IData)(vlSelfRef.__Vdfg_Regularize_706)))
                     : ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3))
                         ? vlSelfRef.soc_b__DOT__mem_rdata
                         : ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3))
                             ? (((- (::IData)((1U & 
                                               ((::IData)(vlSelfRef.__Vdfg_Regularize_707) 
                                                >> 0x0000000fU)))) 
                                 << 0x00000010U) | (::IData)(vlSelfRef.__Vdfg_Regularize_707))
                             : (((- (::IData)((1U & 
                                               ((::IData)(vlSelfRef.__Vdfg_Regularize_706) 
                                                >> 7U)))) 
                                 << 8U) | (::IData)(vlSelfRef.__Vdfg_Regularize_706))))) 
                   & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_710))));
            __Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62 
                = (0x0000001fU & ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_rd) 
                                  & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_710)))));
        } else {
            __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61 
                = (((4U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                     ? ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                         ? ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                             ? vlSelfRef.soc_b__DOT__u_core__DOT__rmd
                             : ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__r_neg)
                                 ? ((::IData)(1U) + 
                                    (~ vlSelfRef.soc_b__DOT__u_core__DOT__rmd))
                                 : vlSelfRef.soc_b__DOT__u_core__DOT__rmd))
                         : ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                             ? vlSelfRef.soc_b__DOT__u_core__DOT__quo
                             : ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__q_neg)
                                 ? ((::IData)(1U) + 
                                    (~ vlSelfRef.soc_b__DOT__u_core__DOT__quo))
                                 : vlSelfRef.soc_b__DOT__u_core__DOT__quo)))
                     : ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                         ? ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                             ? (::IData)((vlSelfRef.soc_b__DOT__u_core__DOT__prod_u 
                                          >> 0x00000020U))
                             : vlSelfRef.__Vdfg_Regularize_714)
                         : ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))
                             ? vlSelfRef.__Vdfg_Regularize_714
                             : (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__prod_u)))) 
                   & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_711))));
            __Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62 
                = (0x0000001fU & ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_rd) 
                                  & (- (::IData)((::IData)(vlSelfRef.__Vdfg_Regularize_711)))));
        }
        __Vdly_Set__soc_b__DOT__u_core__DOT__regs_63 = 1U;
    }
    vlSelfRef.__VprimaryPorts.dbg_tx_valid = 0U;
    vlSelfRef.soc_b__DOT__ram_q = vlSelfRef.soc_b__DOT__ram
        [(0x00003fffU & (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                         >> 2U))];
    vlSelfRef.soc_b__DOT__sel_ram_q = (0U == (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                              >> 0x0000001cU));
    if ((((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid) 
          & (1U == (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                    >> 0x0000001cU))) & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r)))) {
        if ((0U != (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
            if ((0x10U == (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
                if ((1U & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r)) {
                    __Vdly__soc_b__DOT__hw_cnt_5 = 0U;
                }
            }
        }
    }
    vlSelfRef.soc_b__DOT__per_q = ((0U == (0x000000ffU 
                                           & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))
                                    ? (::IData)(vlSelfRef.soc_b__DOT__rx_hold)
                                    : ((4U == (0x000000ffU 
                                               & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))
                                        ? (((::IData)(vlSelfRef.soc_b__DOT__rx_full) 
                                            << 1U) 
                                           | (0U != (::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__n)))
                                        : ((0x14U == 
                                            (0x000000ffU 
                                             & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))
                                            ? vlSelfRef.soc_b__DOT__hw_cnt
                                            : ((- (::IData)(
                                                            (0x20U 
                                                             == 
                                                             (0x000000ffU 
                                                              & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r)))) 
                                               & (::IData)(vlSelfRef.soc_b__DOT__led_r)))));
    vlSelfRef.soc_b__DOT__u_tx__DOT__c = __Vdly__soc_b__DOT__u_tx__DOT__c_22;
    vlSelfRef.soc_b__DOT__u_tx__DOT__sh = __Vdly__soc_b__DOT__u_tx__DOT__sh_20;
    if (vlSelfRef.__VprimaryPorts.resetn) {
        if ((1U & (~ (::IData)(vlSelfRef.__VprimaryPorts.dbg_trap)))) {
            __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23 
                = (1ULL + vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle);
            if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if (vlSelfRef.soc_b__DOT__u_core__DOT__bad) {
                            __Vdly__dbg_trap_35 = 1U;
                        }
                    }
                }
                if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 
                                = (1ULL + vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret);
                        }
                        if ((0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 
                                = (0x0000003fU & ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt) 
                                                  - (::IData)(1U)));
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__md_is_div) {
                                __Vdly__soc_b__DOT__u_core__DOT__quo_28 
                                    = ((vlSelfRef.soc_b__DOT__u_core__DOT__quo 
                                        << 1U) | (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd_ge));
                            }
                        }
                    } else {
                        __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 
                            = (1ULL + vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret);
                    }
                } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)))) {
                            if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)))) {
                                __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 
                                    = (1ULL + vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret);
                            }
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                if ((0x00004000U & vlSelfRef.soc_b__DOT__mem_rdata)) {
                                    __Vdly__soc_b__DOT__u_core__DOT__quo_28 = 0U;
                                    if ((0U == vlSelfRef.soc_b__DOT__u_core__DOT__rv2)) {
                                        __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = 0U;
                                        __Vdly__soc_b__DOT__u_core__DOT__quo_28 = 0xffffffffU;
                                    } else {
                                        __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = 0x20U;
                                    }
                                } else {
                                    __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = 0U;
                                }
                            }
                        }
                    }
                }
            }
            if ((4U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                __Vdly__soc_b__DOT__u_core__DOT__state_24 
                    = ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))
                        ? 0U : ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))
                                 ? 0U : 2U));
            } else if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                        __Vdly__soc_b__DOT__u_core__DOT__state_24 = 0U;
                    }
                } else {
                    __Vdly__soc_b__DOT__u_core__DOT__state_24 = 0U;
                }
            } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                    __Vdly__soc_b__DOT__u_core__DOT__state_24 
                        = ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)
                            ? 4U : ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)
                                     ? 3U : 0U));
                }
            } else {
                __Vdly__soc_b__DOT__u_core__DOT__state_24 = 1U;
            }
        }
        vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle 
            = __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23;
        vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret 
            = __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31;
    } else {
        __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23 = 0ULL;
        vlSelfRef.soc_b__DOT__u_core__DOT__cnt_cycle 
            = __Vdly__soc_b__DOT__u_core__DOT__cnt_cycle_23;
        __Vdly__dbg_trap_35 = 0U;
        __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31 = 0ULL;
        vlSelfRef.soc_b__DOT__u_core__DOT__cnt_instret 
            = __Vdly__soc_b__DOT__u_core__DOT__cnt_instret_31;
        __Vdly__soc_b__DOT__u_core__DOT__state_24 = 0U;
        __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29 = 0U;
    }
    vlSelfRef.soc_b__DOT__u_core__DOT__quo = __Vdly__soc_b__DOT__u_core__DOT__quo_28;
    if (__Vdly_Set__soc_b__DOT__u_core__DOT__regs_63) {
        vlSelfRef.soc_b__DOT__u_core__DOT__regs[__Vdly_Dim0__soc_b__DOT__u_core__DOT__regs_62] 
            = __Vdly_Val__soc_b__DOT__u_core__DOT__regs_61;
    }
    if (__Vdly_Set__soc_b__DOT__ram_51) {
        vlSelfRef.soc_b__DOT__ram[__Vdly_Dim0__soc_b__DOT__ram_50] 
            = ((0xffffff00U & vlSelfRef.soc_b__DOT__ram
                [__Vdly_Dim0__soc_b__DOT__ram_50]) 
               | (::IData)(__Vdly_Val__soc_b__DOT__ram_49));
    }
    if (__Vdly_Set__soc_b__DOT__ram_54) {
        vlSelfRef.soc_b__DOT__ram[__Vdly_Dim0__soc_b__DOT__ram_53] 
            = ((0xffff00ffU & vlSelfRef.soc_b__DOT__ram
                [__Vdly_Dim0__soc_b__DOT__ram_53]) 
               | ((::IData)(__Vdly_Val__soc_b__DOT__ram_52) 
                  << 8U));
    }
    if (__Vdly_Set__soc_b__DOT__ram_57) {
        vlSelfRef.soc_b__DOT__ram[__Vdly_Dim0__soc_b__DOT__ram_56] 
            = ((0xff00ffffU & vlSelfRef.soc_b__DOT__ram
                [__Vdly_Dim0__soc_b__DOT__ram_56]) 
               | ((::IData)(__Vdly_Val__soc_b__DOT__ram_55) 
                  << 0x00000010U));
    }
    if (__Vdly_Set__soc_b__DOT__ram_60) {
        vlSelfRef.soc_b__DOT__ram[__Vdly_Dim0__soc_b__DOT__ram_59] 
            = ((0x00ffffffU & vlSelfRef.soc_b__DOT__ram
                [__Vdly_Dim0__soc_b__DOT__ram_59]) 
               | ((::IData)(__Vdly_Val__soc_b__DOT__ram_58) 
                  << 0x00000018U));
    }
    if ((1U & (~ (::IData)(vlSelfRef.__VprimaryPorts.resetn)))) {
        __Vdly__soc_b__DOT__hw_cnt_5 = 0U;
    }
    vlSelfRef.soc_b__DOT__hw_cnt = __Vdly__soc_b__DOT__hw_cnt_5;
    vlSelfRef.soc_b__DOT__u_tx__DOT__n = __Vdly__soc_b__DOT__u_tx__DOT__n_21;
    vlSelfRef.__VprimaryPorts.uart_tx = (1U & (::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__sh));
    vlSelfRef.soc_b__DOT__tx_start = 0U;
    if ((((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid) 
          & (1U == (vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                    >> 0x0000001cU))) & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r)))) {
        if ((0U == (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
            vlSelfRef.__VprimaryPorts.dbg_tx_valid = 1U;
            vlSelfRef.__VprimaryPorts.dbg_tx_byte = 
                (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r);
            vlSelfRef.soc_b__DOT__tx_start = 1U;
            vlSelfRef.soc_b__DOT__tx_byte = (0x000000ffU 
                                             & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r);
        }
        if ((0U != (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
            if ((0x10U == (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
                vlSelfRef.soc_b__DOT__hw_run = (1U 
                                                & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r);
            }
            if ((0x10U != (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
                if ((0x20U == (0x000000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) {
                    vlSelfRef.soc_b__DOT__led_r = (0x0000003fU 
                                                   & vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r);
                }
            }
        }
    }
    if (vlSelfRef.__VprimaryPorts.resetn) {
        if ((1U & (~ (::IData)(vlSelfRef.__VprimaryPorts.dbg_trap)))) {
            if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                          >> 2U)))) {
                if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if ((0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__md_is_div) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__dvd 
                                    = (vlSelfRef.soc_b__DOT__u_core__DOT__dvd 
                                       << 1U);
                            }
                        }
                        if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__valid_r = 1U;
                        }
                    } else {
                        vlSelfRef.soc_b__DOT__u_core__DOT__valid_r = 1U;
                    }
                } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)))) {
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                if ((0x00004000U & vlSelfRef.soc_b__DOT__mem_rdata)) {
                                    vlSelfRef.soc_b__DOT__u_core__DOT__dvd 
                                        = ((0U == vlSelfRef.soc_b__DOT__u_core__DOT__rv2)
                                            ? 0U : 
                                           (((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__div_signed_d) 
                                             & (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                >> 0x1fU))
                                             ? ((::IData)(1U) 
                                                + (~ vlSelfRef.soc_b__DOT__u_core__DOT__rv1))
                                             : vlSelfRef.soc_b__DOT__u_core__DOT__rv1));
                                }
                            }
                        }
                        if (vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__valid_r = 1U;
                        } else if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)))) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__valid_r = 1U;
                        }
                    }
                }
                if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__ld_off 
                                    = (3U & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr);
                            }
                            if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)))) {
                                if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                    vlSelfRef.soc_b__DOT__u_core__DOT__md_b 
                                        = vlSelfRef.soc_b__DOT__u_core__DOT__rv2;
                                    vlSelfRef.soc_b__DOT__u_core__DOT__md_a 
                                        = vlSelfRef.soc_b__DOT__u_core__DOT__rv1;
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        vlSelfRef.soc_b__DOT__u_core__DOT__valid_r = 1U;
    }
    vlSelfRef.soc_b__DOT__u_core__DOT__prod_u = ((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_b)) 
                                                 * (::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_a)));
    if (vlSelfRef.soc_b__DOT__u_rx__DOT__valid) {
        vlSelfRef.soc_b__DOT__rx_hold = vlSelfRef.soc_b__DOT__u_rx__DOT__data;
        vlSelfRef.soc_b__DOT__rx_full = 1U;
    }
    if ((((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid) 
          & (0x10000000U == (0xf00000ffU & vlSelfRef.soc_b__DOT__u_core__DOT__addr_r))) 
         & (0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r)))) {
        vlSelfRef.soc_b__DOT__rx_full = 0U;
    }
    if (vlSelfRef.__VprimaryPorts.resetn) {
        if ((1U & (~ (::IData)(vlSelfRef.__VprimaryPorts.dbg_trap)))) {
            if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                          >> 2U)))) {
                if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state)))) {
                        vlSelfRef.soc_b__DOT__u_core__DOT__ld_is = 0U;
                    }
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                = vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret;
                            vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                = vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret;
                        }
                        if ((0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__md_is_div) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__rmd 
                                    = ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd_ge)
                                        ? ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh) 
                                           - vlSelfRef.soc_b__DOT__u_core__DOT__dvs)
                                        : (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh));
                            }
                        }
                    } else {
                        vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                            = vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret;
                        vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                            = vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret;
                    }
                } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                        if (vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__ld_is 
                                = (3U == (0x0000007fU 
                                          & vlSelfRef.soc_b__DOT__mem_rdata));
                            vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                = (0xfffffffcU & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr);
                        } else if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)))) {
                            vlSelfRef.soc_b__DOT__u_core__DOT__addr_r 
                                = vlSelfRef.soc_b__DOT__u_core__DOT__next_pc;
                        }
                        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)))) {
                            if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)))) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                    = vlSelfRef.soc_b__DOT__u_core__DOT__next_pc;
                            }
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                if ((0x00004000U & vlSelfRef.soc_b__DOT__mem_rdata)) {
                                    vlSelfRef.soc_b__DOT__u_core__DOT__rmd = 0U;
                                    if ((0U == vlSelfRef.soc_b__DOT__u_core__DOT__rv2)) {
                                        vlSelfRef.soc_b__DOT__u_core__DOT__rmd 
                                            = (((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__div_signed_d) 
                                                & (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                   >> 0x1fU))
                                                ? ((::IData)(1U) 
                                                   + 
                                                   (~ vlSelfRef.soc_b__DOT__u_core__DOT__rv1))
                                                : vlSelfRef.soc_b__DOT__u_core__DOT__rv1);
                                    }
                                }
                            }
                        }
                    }
                }
                if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                            if (vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__ld_f3 
                                    = (7U & (vlSelfRef.soc_b__DOT__mem_rdata 
                                             >> 0x0000000cU));
                                vlSelfRef.soc_b__DOT__u_core__DOT__ld_rd 
                                    = (0x0000001fU 
                                       & (vlSelfRef.soc_b__DOT__mem_rdata 
                                          >> 7U));
                                vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r 
                                    = ((0U == (7U & 
                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                >> 0x0000000cU)))
                                        ? ((vlSelfRef.soc_b__DOT__u_core__DOT__rv2 
                                            << 0x00000018U) 
                                           | ((0x00ff0000U 
                                               & (vlSelfRef.soc_b__DOT__u_core__DOT__rv2 
                                                  << 0x00000010U)) 
                                              | ((0x0000ff00U 
                                                  & (vlSelfRef.soc_b__DOT__u_core__DOT__rv2 
                                                     << 8U)) 
                                                 | (0x000000ffU 
                                                    & vlSelfRef.soc_b__DOT__u_core__DOT__rv2))))
                                        : ((1U == (7U 
                                                   & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                      >> 0x0000000cU)))
                                            ? ((vlSelfRef.soc_b__DOT__u_core__DOT__rv2 
                                                << 0x00000010U) 
                                               | (0x0000ffffU 
                                                  & vlSelfRef.soc_b__DOT__u_core__DOT__rv2))
                                            : vlSelfRef.soc_b__DOT__u_core__DOT__rv2));
                                vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret 
                                    = vlSelfRef.soc_b__DOT__u_core__DOT__next_pc;
                            } else if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                vlSelfRef.soc_b__DOT__u_core__DOT__pc_ret 
                                    = vlSelfRef.soc_b__DOT__u_core__DOT__next_pc;
                            }
                            if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)))) {
                                if (vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) {
                                    vlSelfRef.soc_b__DOT__u_core__DOT__md_rd 
                                        = (0x0000001fU 
                                           & (vlSelfRef.soc_b__DOT__mem_rdata 
                                              >> 7U));
                                    vlSelfRef.soc_b__DOT__u_core__DOT__md_f3 
                                        = (7U & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                 >> 0x0000000cU));
                                    if ((0x00004000U 
                                         & vlSelfRef.soc_b__DOT__mem_rdata)) {
                                        vlSelfRef.soc_b__DOT__u_core__DOT__r_neg 
                                            = (::IData)(
                                                        ((0x00006000U 
                                                          == 
                                                          (0x00007000U 
                                                           & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                         & (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                            >> 0x0000001fU)));
                                        vlSelfRef.soc_b__DOT__u_core__DOT__q_neg 
                                            = (::IData)(
                                                        ((0x00004000U 
                                                          == 
                                                          (0x00007000U 
                                                           & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                         & (((vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                              ^ vlSelfRef.soc_b__DOT__u_core__DOT__rv2) 
                                                             >> 0x1fU) 
                                                            & (0U 
                                                               != vlSelfRef.soc_b__DOT__u_core__DOT__rv2))));
                                        vlSelfRef.soc_b__DOT__u_core__DOT__dvs 
                                            = (((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__div_signed_d) 
                                                & (vlSelfRef.soc_b__DOT__u_core__DOT__rv2 
                                                   >> 0x1fU))
                                                ? ((::IData)(1U) 
                                                   + 
                                                   (~ vlSelfRef.soc_b__DOT__u_core__DOT__rv2))
                                                : vlSelfRef.soc_b__DOT__u_core__DOT__rv2);
                                    }
                                    vlSelfRef.soc_b__DOT__u_core__DOT__md_is_div 
                                        = (1U & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                 >> 0x0000000eU));
                                }
                            }
                        }
                    }
                }
            }
            if ((4U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                if ((1U & (~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state)))) {
                        vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r = 0U;
                    }
                }
            } else if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                    if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt))) {
                        vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r = 0U;
                    }
                } else {
                    vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r = 0U;
                }
            } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state))) {
                if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad)))) {
                    if (vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) {
                        vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r 
                            = ((0x23U == (0x0000007fU 
                                          & vlSelfRef.soc_b__DOT__mem_rdata))
                                ? (0x0000000fU & ((0U 
                                                   == 
                                                   (7U 
                                                    & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                       >> 0x0000000cU)))
                                                   ? 
                                                  ((::IData)(1U) 
                                                   << 
                                                   (3U 
                                                    & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr))
                                                   : 
                                                  (((2U 
                                                     & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr)
                                                     ? 0x0cU
                                                     : 3U) 
                                                   | (- (::IData)(
                                                                  (1U 
                                                                   != 
                                                                   (7U 
                                                                    & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                       >> 0x0000000cU))))))))
                                : 0U);
                    } else if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv)))) {
                        vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r = 0U;
                    }
                }
            }
        }
    } else {
        vlSelfRef.soc_b__DOT__u_core__DOT__ld_is = 0U;
        vlSelfRef.soc_b__DOT__u_core__DOT__pc = 0U;
        vlSelfRef.soc_b__DOT__u_core__DOT__addr_r = 0U;
        vlSelfRef.soc_b__DOT__u_core__DOT__wdata_r = 0U;
        vlSelfRef.soc_b__DOT__u_core__DOT__wstrb_r = 0U;
    }
    if ((1U & (~ (::IData)(vlSelfRef.__VprimaryPorts.resetn)))) {
        vlSelfRef.soc_b__DOT__sel_ram_q = 1U;
        vlSelfRef.soc_b__DOT__hw_run = 0U;
        vlSelfRef.soc_b__DOT__rx_full = 0U;
        vlSelfRef.soc_b__DOT__led_r = 0U;
    }
    vlSelfRef.__Vdfg_Regularize_710 = ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_is) 
                                       & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_rd)));
    vlSelfRef.__Vdfg_Regularize_714 = (::IData)((((vlSelfRef.soc_b__DOT__u_core__DOT__prod_u 
                                                   - 
                                                   (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_b)) 
                                                     << 0x00000020U) 
                                                    & (- (::QData)((::IData)(
                                                                             (((1U 
                                                                                == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3)) 
                                                                               | (2U 
                                                                                == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))) 
                                                                              & (vlSelfRef.soc_b__DOT__u_core__DOT__md_a 
                                                                                >> 0x0000001fU))))))) 
                                                  - 
                                                  (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_a)) 
                                                    << 0x00000020U) 
                                                   & (- (::QData)((::IData)(
                                                                            ((1U 
                                                                              == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3)) 
                                                                             & (vlSelfRef.soc_b__DOT__u_core__DOT__md_b 
                                                                                >> 0x0000001fU))))))) 
                                                 >> 0x00000020U));
    vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh = (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd)) 
                                                  << 1U) 
                                                 | (::QData)((::IData)(
                                                                       (vlSelfRef.soc_b__DOT__u_core__DOT__dvd 
                                                                        >> 0x0000001fU))));
    vlSelfRef.soc_b__DOT__u_rx__DOT__valid = 0U;
    if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__st))) {
        if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__st))) {
            if ((0U != (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c))) {
                __Vdly__soc_b__DOT__u_rx__DOT__c_17 
                    = (0x000001ffU & ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c) 
                                      - (::IData)(1U)));
            }
            if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c))) {
                __Vdly__soc_b__DOT__u_rx__DOT__st_16 = 0U;
                if (vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s) {
                    vlSelfRef.soc_b__DOT__u_rx__DOT__data 
                        = vlSelfRef.soc_b__DOT__u_rx__DOT__sh;
                    vlSelfRef.soc_b__DOT__u_rx__DOT__valid = 1U;
                }
            }
        } else if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c))) {
            __Vdly__soc_b__DOT__u_rx__DOT__c_17 = 0x000000e9U;
            if ((1U == (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__n))) {
                __Vdly__soc_b__DOT__u_rx__DOT__st_16 = 3U;
            }
        } else {
            __Vdly__soc_b__DOT__u_rx__DOT__c_17 = (0x000001ffU 
                                                   & ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c) 
                                                      - (::IData)(1U)));
        }
        if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__st)))) {
            if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c))) {
                __Vdly__soc_b__DOT__u_rx__DOT__sh_18 
                    = (((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s) 
                        << 7U) | (0x0000007fU & ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__sh) 
                                                 >> 1U)));
                if ((1U != (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__n))) {
                    vlSelfRef.soc_b__DOT__u_rx__DOT__n 
                        = (0x0000000fU & ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__n) 
                                          - (::IData)(1U)));
                }
            }
        }
    } else if ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__st))) {
        if ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c))) {
            if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s)))) {
                __Vdly__soc_b__DOT__u_rx__DOT__c_17 = 0x00e9U;
                vlSelfRef.soc_b__DOT__u_rx__DOT__n = 8U;
            }
            __Vdly__soc_b__DOT__u_rx__DOT__st_16 = 
                ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s)
                  ? 0U : 2U);
        } else {
            __Vdly__soc_b__DOT__u_rx__DOT__c_17 = (0x000001ffU 
                                                   & ((::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__c) 
                                                      - (::IData)(1U)));
        }
    } else if ((1U & (~ (::IData)(vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s)))) {
        __Vdly__soc_b__DOT__u_rx__DOT__c_17 = 0x0074U;
        __Vdly__soc_b__DOT__u_rx__DOT__st_16 = 1U;
    }
    vlSelfRef.__VprimaryPorts.led = (0x0000003fU & 
                                     (~ (::IData)(vlSelfRef.soc_b__DOT__led_r)));
    vlSelfRef.soc_b__DOT__u_rx__DOT__sh = __Vdly__soc_b__DOT__u_rx__DOT__sh_18;
    vlSelfRef.soc_b__DOT__u_rx__DOT__st = __Vdly__soc_b__DOT__u_rx__DOT__st_16;
    vlSelfRef.soc_b__DOT__u_rx__DOT__c = __Vdly__soc_b__DOT__u_rx__DOT__c_17;
    vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt = __Vdly__soc_b__DOT__u_core__DOT__md_cnt_29;
    vlSelfRef.soc_b__DOT__mem_rdata = ((::IData)(vlSelfRef.soc_b__DOT__sel_ram_q)
                                        ? vlSelfRef.soc_b__DOT__ram_q
                                        : vlSelfRef.soc_b__DOT__per_q);
    vlSelfRef.soc_b__DOT__u_core__DOT__rmd_ge = (vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh 
                                                 >= (::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__dvs)));
    vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s = vlSelfRef.soc_b__DOT__u_rx__DOT__rx_q;
    vlSelfRef.soc_b__DOT__u_core__DOT__div_signed_d 
        = ((4U == (7U & (vlSelfRef.soc_b__DOT__mem_rdata 
                         >> 0x0000000cU))) | (6U == 
                                              (7U & 
                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                >> 0x0000000cU))));
    if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))) {
        vlSelfRef.__Vdfg_Regularize_706 = (0x000000ffU 
                                           & ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))
                                               ? (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 0x00000018U)
                                               : (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 0x00000010U)));
        vlSelfRef.__Vdfg_Regularize_707 = (0x0000ffffU 
                                           & (vlSelfRef.soc_b__DOT__mem_rdata 
                                              >> 0x00000010U));
    } else {
        vlSelfRef.__Vdfg_Regularize_706 = (0x000000ffU 
                                           & ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))
                                               ? (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 8U)
                                               : vlSelfRef.soc_b__DOT__mem_rdata));
        vlSelfRef.__Vdfg_Regularize_707 = (0x0000ffffU 
                                           & vlSelfRef.soc_b__DOT__mem_rdata);
    }
    vlSelfRef.__Vdfg_Regularize_716 = (::IData)((3U 
                                                 == 
                                                 (0x0000000bU 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)));
    __Vdfg_Regularize_717 = (1U & ((~ (vlSelfRef.soc_b__DOT__mem_rdata 
                                       >> 2U)) | (~ 
                                                  (3U 
                                                   == 
                                                   (3U 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata)))));
    __Vdfg_Regularize_719 = (1U & ((0U != (0x0000000cU 
                                           & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                   | (~ (3U == (3U 
                                                & vlSelfRef.soc_b__DOT__mem_rdata)))));
    soc_b__DOT__u_core__DOT__is_csr = ((0x73U == (0x0000007fU 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                       & (0U != (7U 
                                                 & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                    >> 0x0000000cU))));
    vlSelfRef.soc_b__DOT__u_core__DOT__rv2 = ((0U == 
                                               (0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x00000014U)))
                                               ? 0U
                                               : vlSelfRef.soc_b__DOT__u_core__DOT__regs
                                              [(0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x00000014U))]);
    soc_b__DOT__u_core__DOT__imm_i = (((- (::IData)(
                                                    (vlSelfRef.soc_b__DOT__mem_rdata 
                                                     >> 0x0000001fU))) 
                                       << 0x0000000cU) 
                                      | (vlSelfRef.soc_b__DOT__mem_rdata 
                                         >> 0x00000014U));
    vlSelfRef.soc_b__DOT__u_core__DOT__rv1 = ((0U == 
                                               (0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x0000000fU)))
                                               ? 0U
                                               : vlSelfRef.soc_b__DOT__u_core__DOT__regs
                                              [(0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x0000000fU))]);
    vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv = (::IData)(
                                                             (0x02000033U 
                                                              == 
                                                              (0xfe00007fU 
                                                               & vlSelfRef.soc_b__DOT__mem_rdata)));
    vlSelfRef.__VprimaryPorts.dbg_trap = __Vdly__dbg_trap_35;
    vlSelfRef.soc_b__DOT__u_core__DOT__state = __Vdly__soc_b__DOT__u_core__DOT__state_24;
    vlSelfRef.soc_b__DOT__u_core__DOT__acc_data = (
                                                   (0x23U 
                                                    == 
                                                    (0x0000007fU 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                   | (3U 
                                                      == 
                                                      (0x0000007fU 
                                                       & vlSelfRef.soc_b__DOT__mem_rdata)));
    if ((0x13U == (0x0000007fU & vlSelfRef.soc_b__DOT__mem_rdata))) {
        soc_b__DOT__u_core__DOT__shamt = (0x0000001fU 
                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                             >> 0x00000014U));
        soc_b__DOT__u_core__DOT__alu_b = soc_b__DOT__u_core__DOT__imm_i;
    } else {
        soc_b__DOT__u_core__DOT__shamt = (0x0000001fU 
                                          & vlSelfRef.soc_b__DOT__u_core__DOT__rv2);
        soc_b__DOT__u_core__DOT__alu_b = vlSelfRef.soc_b__DOT__u_core__DOT__rv2;
    }
    soc_b__DOT__u_core__DOT__ld_addr = (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                        + soc_b__DOT__u_core__DOT__imm_i);
    vlSelfRef.soc_b__DOT__u_rx__DOT__rx_q = vlSelfRef.__VprimaryPorts.uart_rx;
    vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid = 
        ((~ (::IData)(vlSelfRef.__VprimaryPorts.dbg_trap)) 
         & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__valid_r));
    vlSelfRef.__Vdfg_Regularize_711 = ((3U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state)) 
                                       & ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt)) 
                                          & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_rd))));
    soc_b__DOT__u_core__DOT__lt_s = VL_LTS_III(32, vlSelfRef.soc_b__DOT__u_core__DOT__rv1, soc_b__DOT__u_core__DOT__alu_b);
    soc_b__DOT__u_core__DOT__lt_u = (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                     < soc_b__DOT__u_core__DOT__alu_b);
    vlSelfRef.soc_b__DOT__u_core__DOT__d_addr = ((0x23U 
                                                  == 
                                                  (0x0000007fU 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata))
                                                  ? 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  + 
                                                  (((- (::IData)(
                                                                 (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x0000001fU))) 
                                                    << 0x0000000cU) 
                                                   | ((0x00000fe0U 
                                                       & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x00000014U)) 
                                                      | (0x0000001fU 
                                                         & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 7U)))))
                                                  : soc_b__DOT__u_core__DOT__ld_addr);
    vlSelfRef.__Vdfg_Regularize_715 = (((0x00004000U 
                                         & vlSelfRef.soc_b__DOT__mem_rdata)
                                         ? ((0x00002000U 
                                             & vlSelfRef.soc_b__DOT__mem_rdata)
                                             ? ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 & soc_b__DOT__u_core__DOT__alu_b)
                                                 : 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 | soc_b__DOT__u_core__DOT__alu_b))
                                             : ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                ((0x40000000U 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)
                                                  ? 
                                                 VL_SHIFTRS_III(32,32,5, vlSelfRef.soc_b__DOT__u_core__DOT__rv1, (::IData)(soc_b__DOT__u_core__DOT__shamt))
                                                  : 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  >> (::IData)(soc_b__DOT__u_core__DOT__shamt)))
                                                 : 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 ^ soc_b__DOT__u_core__DOT__alu_b)))
                                         : ((0x00002000U 
                                             & vlSelfRef.soc_b__DOT__mem_rdata)
                                             ? ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? (::IData)(soc_b__DOT__u_core__DOT__lt_u)
                                                 : (::IData)(soc_b__DOT__u_core__DOT__lt_s))
                                             : ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 << (::IData)(soc_b__DOT__u_core__DOT__shamt))
                                                 : 
                                                ((::IData)(
                                                           (0x40000033U 
                                                            == 
                                                            (0x4000007fU 
                                                             & vlSelfRef.soc_b__DOT__mem_rdata)))
                                                  ? 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  - soc_b__DOT__u_core__DOT__alu_b)
                                                  : 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  + soc_b__DOT__u_core__DOT__alu_b))))) 
                                       & (- (::IData)(
                                                      (3U 
                                                       == 
                                                       (3U 
                                                        & vlSelfRef.soc_b__DOT__mem_rdata)))));
    vlSelfRef.soc_b__DOT__u_core__DOT__next_pc = ((0x6fU 
                                                   == 
                                                   (0x0000007fU 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata))
                                                   ? 
                                                  (vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                                   + 
                                                   ((((0x00000ffeU 
                                                       & ((- (::IData)(
                                                                       (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                        >> 0x0000001fU))) 
                                                          << 1U)) 
                                                      | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                         >> 0x0000001fU)) 
                                                     << 0x00000014U) 
                                                    | ((((0x000001feU 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x0000000bU)) 
                                                         | (1U 
                                                            & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                               >> 0x00000014U))) 
                                                        << 0x0000000bU) 
                                                       | (0x000007feU 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x00000014U)))))
                                                   : 
                                                  ((0x67U 
                                                    == 
                                                    (0x0000007fU 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata))
                                                    ? 
                                                   (0xfffffffeU 
                                                    & soc_b__DOT__u_core__DOT__ld_addr)
                                                    : 
                                                   ((0x63U 
                                                     == 
                                                     (0x0000007fU 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))
                                                     ? 
                                                    ((1U 
                                                      & ((0x00004000U 
                                                          & vlSelfRef.soc_b__DOT__mem_rdata)
                                                          ? 
                                                         ((0x00002000U 
                                                           & vlSelfRef.soc_b__DOT__mem_rdata)
                                                           ? 
                                                          ((0x00001000U 
                                                            & vlSelfRef.soc_b__DOT__mem_rdata)
                                                            ? 
                                                           (~ (::IData)(soc_b__DOT__u_core__DOT__lt_u))
                                                            : (::IData)(soc_b__DOT__u_core__DOT__lt_u))
                                                           : 
                                                          ((0x00001000U 
                                                            & vlSelfRef.soc_b__DOT__mem_rdata)
                                                            ? 
                                                           (~ (::IData)(soc_b__DOT__u_core__DOT__lt_s))
                                                            : (::IData)(soc_b__DOT__u_core__DOT__lt_s)))
                                                          : 
                                                         ((~ 
                                                           (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 0x0000000dU)) 
                                                          & ((0x00001000U 
                                                              & vlSelfRef.soc_b__DOT__mem_rdata)
                                                              ? 
                                                             (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                              != vlSelfRef.soc_b__DOT__u_core__DOT__rv2)
                                                              : 
                                                             (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                              == vlSelfRef.soc_b__DOT__u_core__DOT__rv2)))))
                                                      ? 
                                                     (vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                                      + 
                                                      (((- (::IData)(
                                                                     (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                      >> 0x0000001fU))) 
                                                        << 0x0000000dU) 
                                                       | ((((2U 
                                                             & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                >> 0x0000001eU)) 
                                                            | (1U 
                                                               & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 7U))) 
                                                           << 0x0000000bU) 
                                                          | ((0x000007e0U 
                                                              & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                 >> 0x00000014U)) 
                                                             | (0x0000001eU 
                                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                   >> 7U))))))
                                                      : 
                                                     ((::IData)(4U) 
                                                      + vlSelfRef.soc_b__DOT__u_core__DOT__pc))
                                                     : 
                                                    ((::IData)(4U) 
                                                     + vlSelfRef.soc_b__DOT__u_core__DOT__pc))));
    __Vdfg_Regularize_718 = (::IData)(((0x00002000U 
                                        == (0x00007000U 
                                            & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                       & (0U != (3U 
                                                 & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr))));
    vlSelfRef.soc_b__DOT__u_core__DOT__bad = (1U & 
                                              (((0x00000040U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                ((~ 
                                                  (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 5U)) 
                                                 | ((0x00000010U 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)
                                                     ? 
                                                    (((~ 
                                                       ((0x0c00U 
                                                         == 
                                                         (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x00000014U)) 
                                                        | ((0x0c80U 
                                                            == 
                                                            (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x00000014U)) 
                                                           | ((0x0c02U 
                                                               == 
                                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                >> 0x00000014U)) 
                                                              | (0x0c82U 
                                                                 == 
                                                                 (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x00000014U)))))) 
                                                      & (::IData)(soc_b__DOT__u_core__DOT__is_csr)) 
                                                     | (::IData)(__Vdfg_Regularize_719))
                                                     : 
                                                    ((8U 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata)
                                                      ? (::IData)(__Vdfg_Regularize_717)
                                                      : 
                                                     ((~ 
                                                       (3U 
                                                        == 
                                                        (3U 
                                                         & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                      | ((0U 
                                                          != 
                                                          (7U 
                                                           & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                              >> 0x0000000cU))) 
                                                         & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 2U))))))
                                                 : 
                                                ((0x00000020U 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)
                                                  ? 
                                                 ((0x00000010U 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata)
                                                   ? 
                                                  (((4U 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)
                                                     ? 
                                                    (~ 
                                                     (3U 
                                                      == 
                                                      (3U 
                                                       & vlSelfRef.soc_b__DOT__mem_rdata)))
                                                     : 
                                                    (~ 
                                                     ((3U 
                                                       == 
                                                       (3U 
                                                        & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                      & ((1U 
                                                          == 
                                                          (vlSelfRef.soc_b__DOT__mem_rdata 
                                                           >> 0x00000019U)) 
                                                         | ((0U 
                                                             == 
                                                             (vlSelfRef.soc_b__DOT__mem_rdata 
                                                              >> 0x00000019U)) 
                                                            | ((0x20U 
                                                                == 
                                                                (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                 >> 0x00000019U)) 
                                                               & ((5U 
                                                                   == 
                                                                   (7U 
                                                                    & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                       >> 0x0000000cU))) 
                                                                  | (0U 
                                                                     == 
                                                                     (7U 
                                                                      & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                         >> 0x0000000cU)))))))))) 
                                                   | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                      >> 3U))
                                                   : (::IData)(__Vdfg_Regularize_719))
                                                  : 
                                                 ((0x00000010U 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata)
                                                   ? 
                                                  ((~ 
                                                    (3U 
                                                     == 
                                                     (3U 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                   | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                      >> 3U))
                                                   : 
                                                  ((8U 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata)
                                                    ? (::IData)(__Vdfg_Regularize_717)
                                                    : 
                                                   ((vlSelfRef.soc_b__DOT__mem_rdata 
                                                     >> 2U) 
                                                    | ((~ 
                                                        (3U 
                                                         == 
                                                         (3U 
                                                          & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                       | ((6U 
                                                           == 
                                                           (7U 
                                                            & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                               >> 0x0000000cU))) 
                                                          | ((3U 
                                                              == 
                                                              (7U 
                                                               & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x0000000cU))) 
                                                             | (7U 
                                                                == 
                                                                (7U 
                                                                 & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                    >> 0x0000000cU))))))))))) 
                                               | ((((3U 
                                                     == 
                                                     (0x0000007fU 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))
                                                     ? 
                                                    (((1U 
                                                       == 
                                                       (7U 
                                                        & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                           >> 0x0000000cU))) 
                                                      | (5U 
                                                         == 
                                                         (7U 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x0000000cU))))
                                                      ? vlSelfRef.soc_b__DOT__u_core__DOT__d_addr
                                                      : (::IData)(__Vdfg_Regularize_718))
                                                     : 
                                                    ((1U 
                                                      == 
                                                      (7U 
                                                       & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x0000000cU)))
                                                      ? vlSelfRef.soc_b__DOT__u_core__DOT__d_addr
                                                      : (::IData)(__Vdfg_Regularize_718))) 
                                                   & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)) 
                                                  | (::IData)(
                                                              (0x00000073U 
                                                               == 
                                                               (0x0000707fU 
                                                                & vlSelfRef.soc_b__DOT__mem_rdata))))));
    vlSelfRef.__Vdfg_Regularize_712 = ((~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad) 
                                           | ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) 
                                              | ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) 
                                                 | (0U 
                                                    == 
                                                    (0x0000001fU 
                                                     & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                        >> 7U))))))) 
                                       & ((0x00000040U 
                                           & vlSelfRef.soc_b__DOT__mem_rdata)
                                           ? (((0x00000010U 
                                                & vlSelfRef.soc_b__DOT__mem_rdata)
                                                ? (::IData)(
                                                            ((3U 
                                                              == 
                                                              (0x0000000fU 
                                                               & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                             & (::IData)(soc_b__DOT__u_core__DOT__is_csr)))
                                                : (::IData)(
                                                            (7U 
                                                             == 
                                                             (7U 
                                                              & vlSelfRef.soc_b__DOT__mem_rdata)))) 
                                              & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                 >> 5U))
                                           : ((vlSelfRef.soc_b__DOT__mem_rdata 
                                               >> 4U) 
                                              & (::IData)(vlSelfRef.__Vdfg_Regularize_716))));
}

void Vsoc_b___024root___trigger_orInto__act_vec_vec(::VlUnpacked<::QData/*63:0*/, 1> &out, const ::VlUnpacked<::QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    ::IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((::IData)(1U) + n);
    } while ((0U >= n));
}

void Vsoc_b___024root___trigger_clear__act(::VlUnpacked<::QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___trigger_clear__act\n"); );
    // Locals
    ::IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((::IData)(1U) + n);
    } while ((1U > n));
}

#ifdef VL_DEBUG
void Vsoc_b___024root___eval_debug_assertions(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_debug_assertions\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.__VprimaryPorts.clk 
                      & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.__VprimaryPorts.resetn 
                      & 0xfeU)))) {
        Verilated::overWidthError("resetn");
    }
    if (VL_UNLIKELY(((vlSelfRef.__VprimaryPorts.uart_rx 
                      & 0xfeU)))) {
        Verilated::overWidthError("uart_rx");
    }
}
#endif  // VL_DEBUG
