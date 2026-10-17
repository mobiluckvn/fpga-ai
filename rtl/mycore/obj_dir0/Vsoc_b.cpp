// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vsoc_b__pch.h"

//============================================================
// Constructors

Vsoc_b::Vsoc_b(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vsoc_b__Syms(contextp(), _vcname__, this)}
    , m_evalLoop{*this, /*convergeLimit:*/ 10000}
    , clk{vlSymsp->vlInst.TOP.__VprimaryPorts.clk}
    , resetn{vlSymsp->vlInst.TOP.__VprimaryPorts.resetn}
    , uart_tx{vlSymsp->vlInst.TOP.__VprimaryPorts.uart_tx}
    , uart_rx{vlSymsp->vlInst.TOP.__VprimaryPorts.uart_rx}
    , led{vlSymsp->vlInst.TOP.__VprimaryPorts.led}
    , dbg_tx_valid{vlSymsp->vlInst.TOP.__VprimaryPorts.dbg_tx_valid}
    , dbg_tx_byte{vlSymsp->vlInst.TOP.__VprimaryPorts.dbg_tx_byte}
    , dbg_trap{vlSymsp->vlInst.TOP.__VprimaryPorts.dbg_trap}
    , rootp{&(vlSymsp->vlInst.TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vsoc_b::Vsoc_b(const char* _vcname__)
    : Vsoc_b(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vsoc_b::~Vsoc_b() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vsoc_b___024root___eval_debug_assertions(Vsoc_b___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___eval_static(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_initial(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD bool Vsoc_b___024root___eval_stl(Vsoc_b___024root* vlSelf, ::CData/*0:0*/ firstIteration);
void Vsoc_b___024root___eval_sample(Vsoc_b___024root* vlSelf);
bool Vsoc_b___024root___eval_ico(Vsoc_b___024root* vlSelf, ::CData/*0:0*/ firstIteration);
bool Vsoc_b___024root___eval_act(Vsoc_b___024root* vlSelf);
bool Vsoc_b___024root___eval_inact(Vsoc_b___024root* vlSelf);
bool Vsoc_b___024root___eval_nba(Vsoc_b___024root* vlSelf);
bool Vsoc_b___024root___eval_obs(Vsoc_b___024root* vlSelf);
bool Vsoc_b___024root___eval_react(Vsoc_b___024root* vlSelf);
void Vsoc_b___024root___eval_postponed(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_final(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__stl(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__ico(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__act(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__nba(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__obs(Vsoc_b___024root* vlSelf);
VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__react(Vsoc_b___024root* vlSelf);

void Vsoc_b::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vsoc_b::eval_step\n"); );
    m_evalLoop.eval();
}

void Vsoc_b::evalBegin() {
#ifdef VL_DEBUG
    // Debug assertions
    Vsoc_b___024root___eval_debug_assertions(&(vlSymsp->vlInst.TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
}

void Vsoc_b::evalEnd() {
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

void Vsoc_b::evalStatic() {
    Vsoc_b___024root___eval_static(&(vlSymsp->vlInst.TOP));
}

void Vsoc_b::evalInitial() {
    Vsoc_b___024root___eval_initial(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalStl(bool firstIteration) {
    return Vsoc_b___024root___eval_stl(&(vlSymsp->vlInst.TOP), firstIteration);
}

void Vsoc_b::evalSample() {
    Vsoc_b___024root___eval_sample(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalIco(bool firstIteration) {
    return Vsoc_b___024root___eval_ico(&(vlSymsp->vlInst.TOP), firstIteration);
}

bool Vsoc_b::evalAct() {
    return Vsoc_b___024root___eval_act(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalInact() {
    return Vsoc_b___024root___eval_inact(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalNba() {
    return Vsoc_b___024root___eval_nba(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalObs() {
    return Vsoc_b___024root___eval_obs(&(vlSymsp->vlInst.TOP));
}

bool Vsoc_b::evalReact() {
    return Vsoc_b___024root___eval_react(&(vlSymsp->vlInst.TOP));
}

void Vsoc_b::evalPostponed() {
    Vsoc_b___024root___eval_postponed(&(vlSymsp->vlInst.TOP));
}

void Vsoc_b::evalFinal() {
    Vsoc_b___024root___eval_final(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersStl() {
    Vsoc_b___024root___eval_dump_triggers__stl(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersIco() {
    Vsoc_b___024root___eval_dump_triggers__ico(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersAct() {
    Vsoc_b___024root___eval_dump_triggers__act(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersNba() {
    Vsoc_b___024root___eval_dump_triggers__nba(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersObs() {
    Vsoc_b___024root___eval_dump_triggers__obs(&(vlSymsp->vlInst.TOP));
}

VL_ATTR_COLD void Vsoc_b::dumpTriggersReact() {
    Vsoc_b___024root___eval_dump_triggers__react(&(vlSymsp->vlInst.TOP));
}

//============================================================
// Events and timing
bool Vsoc_b::eventsPending() { return false; }

uint64_t Vsoc_b::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vsoc_b::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

VL_ATTR_COLD void Vsoc_b::final() {
    contextp()->executingFinal(true);
    evalFinal();
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vsoc_b::hierName() const { return vlSymsp->name(); }
const char* Vsoc_b::modelName() const { return "Vsoc_b"; }
unsigned Vsoc_b::threads() const { return 1; }
void Vsoc_b::prepareClone() const { contextp()->prepareClone(); }
void Vsoc_b::atClone() const {
    contextp()->threadPoolpOnClone();
}
