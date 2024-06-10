export DESIGN_NAME     	= ChIP4
export VERILOG_FILES 	= ./designs/src/$(DESIGN_NAME)/ChIP4.v ./designs/src/$(DESIGN_NAME)/ChIP.v
export SDC_FILE      	= ./designs/$(PLATFORM)/$(DESIGN_NAME)/constraint.sdc
export IO_CONSTRAINTS	= ./designs/$(PLATFORM)/$(DESIGN_NAME)/io_constraints.tcl

# optional - path to route dimensions specifications
DIMM_FILE = ./designs/$(PLATFORM)/$(DESIGN_NAME)/dimm.csv
SCAD_ARGS += --dimm_file "$(DIMM_FILE)"