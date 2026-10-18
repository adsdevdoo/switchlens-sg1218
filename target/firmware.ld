OUTPUT_ARCH(mips)
OUTPUT_FORMAT("elf32-tradbigmips")
ENTRY(sg_route_compare)
MEMORY { PATCH (rx) : ORIGIN = 0xbfce0640, LENGTH = 125376 }
SECTIONS {
 .text : { *(.text .text.*) } > PATCH
 .rodata : { *(.rodata .rodata.*) } > PATCH
 .data : { *(.data .data.* .sdata .sdata.*) } > PATCH
 .bss : { *(.bss .bss.* .sbss .sbss.* COMMON) } > PATCH
 .forbidden : { *(.got .got.* .got.plt .plt .plt.*) } > PATCH
 . = ALIGN(4);
 __patch_end = .;
 /DISCARD/ : { *(.comment .note.* .eh_frame .eh_frame.* .pdr .reginfo .MIPS.abiflags .gnu.attributes) }
 ASSERT(SIZEOF(.data) == 0, "Patch must not require initialized writable globals")
 ASSERT(SIZEOF(.bss) == 0, "Patch must not reserve unallocated SRAM")
 ASSERT(SIZEOF(.forbidden) == 0, "Unexpected GOT/PLT: use -G0 -mno-abicalls -fno-pic")
 ASSERT(__patch_end <= 0xbfcff000, "Patch exceeds audited FF range")
}
fw_statistics_page = 0xbfc4163c;
fw_strcmp = 0xbfc2bdd8;
fw_http_init = 0xbfc3b278;
fw_http_status = 0xbf01cd38;
fw_http_header = 0xbf01cc5c;
fw_http_raw = 0xbf01cac0;
fw_socket_send = 0xbfc38a64;
fw_register_read = 0xbfc10768;
fw_cli_lookup = 0xbfc2c508;
fw_cli_poll = 0xbfc2cd0c;
fw_cli_help = 0xbfc2d6c0;
fw_cli_reg = 0xbfc2d8d0;
fw_printf = 0xbfc11514;
fw_gpio_write = 0xbf0196b4;
fw_cool_poll = 0xbfc5c368;
fw_http_outer_continue = 0xbfc3ce50;
