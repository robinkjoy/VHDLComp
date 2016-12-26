if exists('g:VHDLComp_loaded')
    finish
else
    let g:VHDLComp_loaded = 1
endif

function! VHDLEnt2comp()
python3 << EOF
import VHDLComp
VHDLComp.vhdl_ent2comp()
EOF
endfunction

function! VHDLEnt2sig()
python3 << EOF
import VHDLComp
VHDLComp.vhdl_ent2sig()
EOF
endfunction

function! VHDLEnt2inst()
python3 << EOF
import VHDLComp
VHDLComp.vhdl_ent2inst()
EOF
endfunction

command! VHDLEnt2comp call VHDLEnt2comp()
command! VHDLEnt2sig call VHDLEnt2sig()
command! VHDLEnt2inst call VHDLEnt2inst()
