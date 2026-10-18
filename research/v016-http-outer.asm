SHA256 c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32
00034e48 bfc3ce48 27bdffe0 addiu    $sp, $sp, -0x20
00034e4c bfc3ce4c afbf001c sw       $ra, 0x1c($sp)
00034e50 bfc3ce50 afb10018 sw       $s1, 0x18($sp)
00034e54 bfc3ce54 afb00014 sw       $s0, 0x14($sp)
00034e58 bfc3ce58 3c02bf01 lui      $v0, 0xbf01
00034e5c bfc3ce5c 8c431660 lw       $v1, 0x1660($v0)
00034e60 bfc3ce60 24020001 addiu    $v0, $zero, 1
00034e64 bfc3ce64 14620019 bne      $v1, $v0, 0xbfc3cecc
00034e68 bfc3ce68 00808821 move     $s1, $a0
00034e6c bfc3ce6c 3c07bf02 lui      $a3, 0xbf02
00034e70 bfc3ce70 24e58df4 addiu    $a1, $a3, -0x720c
00034e74 bfc3ce74 90a20001 lbu      $v0, 1($a1)
00034e78 bfc3ce78 90a60002 lbu      $a2, 2($a1)
00034e7c bfc3ce7c 90830299 lbu      $v1, 0x299($a0)
00034e80 bfc3ce80 9088029a lbu      $t0, 0x29a($a0)
00034e84 bfc3ce84 90ea8df4 lbu      $t2, -0x720c($a3)
00034e88 bfc3ce88 00031a00 sll      $v1, $v1, 8
00034e8c bfc3ce8c 90a70003 lbu      $a3, 3($a1)
00034e90 bfc3ce90 00084400 sll      $t0, $t0, 0x10
00034e94 bfc3ce94 00021200 sll      $v0, $v0, 8
00034e98 bfc3ce98 00063400 sll      $a2, $a2, 0x10
00034e9c bfc3ce9c 90890298 lbu      $t1, 0x298($a0)
00034ea0 bfc3cea0 9085029b lbu      $a1, 0x29b($a0)
00034ea4 bfc3cea4 00681825 or       $v1, $v1, $t0
00034ea8 bfc3cea8 00461025 or       $v0, $v0, $a2
00034eac bfc3ceac 00691825 or       $v1, $v1, $t1
00034eb0 bfc3ceb0 004a1025 or       $v0, $v0, $t2
00034eb4 bfc3ceb4 00052e00 sll      $a1, $a1, 0x18
00034eb8 bfc3ceb8 00073e00 sll      $a3, $a3, 0x18
00034ebc bfc3cebc 00651825 or       $v1, $v1, $a1
00034ec0 bfc3cec0 00471025 or       $v0, $v0, $a3
00034ec4 bfc3cec4 10620019 beq      $v1, $v0, 0xbfc3cf2c
00034ec8 bfc3cec8 24030258 addiu    $v1, $zero, 0x258
00034ecc bfc3cecc 3c05bfce lui      $a1, 0xbfce
00034ed0 bfc3ced0 8e24008c lw       $a0, 0x8c($s1)
00034ed4 bfc3ced4 24a5d924 addiu    $a1, $a1, -0x26dc
00034ed8 bfc3ced8 0ff0af81 jal      0xbfc2be04
00034edc bfc3cedc 2406000a addiu    $a2, $zero, 0xa
00034ee0 bfc3cee0 10400005 beqz     $v0, 0xbfc3cef8
00034ee4 bfc3cee4 26300008 addiu    $s0, $s1, 8
00034ee8 bfc3cee8 3c05bfce lui      $a1, 0xbfce
00034eec bfc3ceec 02202021 move     $a0, $s1
00034ef0 bfc3cef0 0bf0f3ce j        0xbfc3cf38
00034ef4 bfc3cef4 24a5daa0 addiu    $a1, $a1, -0x2560
00034ef8 bfc3cef8 3c05bfce lui      $a1, 0xbfce
00034efc bfc3cefc 24a5d93c addiu    $a1, $a1, -0x26c4
00034f00 bfc3cf00 0ff0af76 jal      0xbfc2bdd8
00034f04 bfc3cf04 02002021 move     $a0, $s0
00034f08 bfc3cf08 50400006 beql     $v0, $zero, 0xbfc3cf24
00034f0c bfc3cf0c 02202021 move     $a0, $s1
00034f10 bfc3cf10 3c05bfce lui      $a1, 0xbfce
00034f14 bfc3cf14 24a5d9e4 addiu    $a1, $a1, -0x261c
00034f18 bfc3cf18 0ff0af76 jal      0xbfc2bdd8
00034f1c bfc3cf1c 02002021 move     $a0, $s0
00034f20 bfc3cf20 02202021 move     $a0, $s1
00034f24 bfc3cf24 0bf0f3ce j        0xbfc3cf38
00034f28 bfc3cf28 02002821 move     $a1, $s0
00034f2c bfc3cf2c 3c02bf01 lui      $v0, 0xbf01
00034f30 bfc3cf30 24850008 addiu    $a1, $a0, 8
00034f34 bfc3cf34 a4431670 sh       $v1, 0x1670($v0)
00034f38 bfc3cf38 0ff0edd0 jal      0xbfc3b740
00034f3c bfc3cf3c 00000000 nop      
00034f40 bfc3cf40 8fbf001c lw       $ra, 0x1c($sp)
00034f44 bfc3cf44 8fb10018 lw       $s1, 0x18($sp)
00034f48 bfc3cf48 8fb00014 lw       $s0, 0x14($sp)
00034f4c bfc3cf4c 00001021 move     $v0, $zero
00034f50 bfc3cf50 03e00008 jr       $ra
00034f54 bfc3cf54 27bd0020 addiu    $sp, $sp, 0x20
