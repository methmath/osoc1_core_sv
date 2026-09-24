SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/../common/cpu_sv_package.sv
VERILOG_SOURCES += $(PWD)/ctrl.sv

TOPLEVEL = ctrl
MODULE = python_stimulus_ctrl

export PYTHONPATH := $(PWD)/../common:$(PYTHONPATH)
COMPILE_ARGS += -g2012
export COCOTB_HDL_TIMEUNIT = 1ns
export COCOTB_HDL_TIMEPRECISION = 1ps

include $(shell cocotb-config --makefiles)/Makefile.sim
