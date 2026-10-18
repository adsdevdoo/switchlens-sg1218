/* The optional outer entry handles exact anonymous GET before session state.
 * Every other request resumes the displaced stock prologue and auth path.
 * v1 carries route identity through the stock epilogue, which does not use it. */
.set noreorder
.set nomips16
.text
#ifdef SG_ANONYMOUS_STATS
.globl sg_http_outer
.ent sg_http_outer
sg_http_outer:
 addiu $sp,$sp,-24
 sw $ra,20($sp)
 sw $a0,16($sp)
 jal sg_is_anonymous_stats
 nop
 lw $a0,16($sp)
 lw $ra,20($sp)
 beqz $v0,3f
 addiu $sp,$sp,24
 j sg_http_entry
 nop
3:
 /* Replay the two overwritten instructions, then stock body at +8. */
 addiu $sp,$sp,-32
 sw $ra,28($sp)
 j fw_http_outer_continue
 nop
.end sg_http_outer
#endif
.globl sg_route_compare
.ent sg_route_compare
sg_route_compare:
 addiu $sp,$sp,-24
 sw $ra,20($sp)
 jal sg_route_kind
 nop
 move $v1,$v0
 sltiu $v0,$v0,2
 xori $v0,$v0,1
 lw $ra,20($sp)
 jr $ra
 addiu $sp,$sp,24
.end sg_route_compare

.globl sg_route_dispatch
.ent sg_route_dispatch
sg_route_dispatch:
 beqz $v1,1f
 nop
 j sg_http_entry
 nop
1:
 j fw_statistics_page
 nop
.end sg_route_dispatch

/* Reject before creating a C frame if less than 3072 bytes remain above the
 * startup-derived end of RAM code. This is not a bound for firmware IRQ use. */
.globl sg_http_entry
.ent sg_http_entry
sg_http_entry:
 lui $t0,0xbf02
 addiu $t0,$t0,-3776 /* BF01F140 = BF01E540 + 3072 */
 sltu $t0,$sp,$t0
 bnez $t0,2f
 nop
 j sg_http_stats
 nop
2:
 jr $ra
 addiu $v0,$zero,-1
.end sg_http_entry
.section .note.GNU-stack,"",@progbits
