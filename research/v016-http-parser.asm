SHA256 c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32
00006c94 bf01d05c 27bdffc8 addiu    $sp, $sp, -0x38
00006c98 bf01d060 afbf0034 sw       $ra, 0x34($sp)
00006c9c bf01d064 afbe0030 sw       $fp, 0x30($sp)
00006ca0 bf01d068 afb7002c sw       $s7, 0x2c($sp)
00006ca4 bf01d06c afb60028 sw       $s6, 0x28($sp)
00006ca8 bf01d070 afb50024 sw       $s5, 0x24($sp)
00006cac bf01d074 afb40020 sw       $s4, 0x20($sp)
00006cb0 bf01d078 afb3001c sw       $s3, 0x1c($sp)
00006cb4 bf01d07c afb20018 sw       $s2, 0x18($sp)
00006cb8 bf01d080 afb10014 sw       $s1, 0x14($sp)
00006cbc bf01d084 afb00010 sw       $s0, 0x10($sp)
00006cc0 bf01d088 00809821 move     $s3, $a0
00006cc4 bf01d08c 00a0b821 move     $s7, $a1
00006cc8 bf01d090 10800194 beqz     $a0, 0xbf01d6e4
00006ccc bf01d094 00c0b021 move     $s6, $a2
00006cd0 bf01d098 10a00195 beqz     $a1, 0xbf01d6f0
00006cd4 bf01d09c 2402ffff addiu    $v0, $zero, -1
00006cd8 bf01d0a0 18c00193 blez     $a2, 0xbf01d6f0
00006cdc bf01d0a4 00a08021 move     $s0, $a1
00006ce0 bf01d0a8 a0800008 sb       $zero, 8($a0)
00006ce4 bf01d0ac a4800150 sh       $zero, 0x150($a0)
00006ce8 bf01d0b0 ae650088 sw       $a1, 0x88($s3)
00006cec bf01d0b4 0000a021 move     $s4, $zero
00006cf0 bf01d0b8 24030020 addiu    $v1, $zero, 0x20
00006cf4 bf01d0bc 92020000 lbu      $v0, ($s0)
00006cf8 bf01d0c0 54430014 bnel     $v0, $v1, 0xbf01d114
00006cfc bf01d0c4 26940001 addiu    $s4, $s4, 1
00006d00 bf01d0c8 3c05bfce lui      $a1, 0xbfce
00006d04 bf01d0cc 24a5d8ec addiu    $a1, $a1, -0x2714
00006d08 bf01d0d0 02e02021 move     $a0, $s7
00006d0c bf01d0d4 0ff0ce98 jal      0xbfc33a60
00006d10 bf01d0d8 24060003 addiu    $a2, $zero, 3
00006d14 bf01d0dc 10400009 beqz     $v0, 0xbf01d104
00006d18 bf01d0e0 24020001 addiu    $v0, $zero, 1
00006d1c bf01d0e4 3c05bfce lui      $a1, 0xbfce
00006d20 bf01d0e8 8e640088 lw       $a0, 0x88($s3)
00006d24 bf01d0ec 24a5d8f0 addiu    $a1, $a1, -0x2710
00006d28 bf01d0f0 0ff0ce98 jal      0xbfc33a60
00006d2c bf01d0f4 24060004 addiu    $a2, $zero, 4
00006d30 bf01d0f8 14400004 bnez     $v0, 0xbf01d10c
00006d34 bf01d0fc 2402ffff addiu    $v0, $zero, -1
00006d38 bf01d100 24020002 addiu    $v0, $zero, 2
00006d3c bf01d104 0bc07448 j        0xbf01d120
00006d40 bf01d108 ae620004 sw       $v0, 4($s3)
00006d44 bf01d10c 0bc075bc j        0xbf01d6f0
00006d48 bf01d110 ae620004 sw       $v0, 4($s3)
00006d4c bf01d114 0296102a slt      $v0, $s4, $s6
00006d50 bf01d118 1440ffe8 bnez     $v0, 0xbf01d0bc
00006d54 bf01d11c 26100001 addiu    $s0, $s0, 1
00006d58 bf01d120 26050001 addiu    $a1, $s0, 1
00006d5c bf01d124 ae65008c sw       $a1, 0x8c($s3)
00006d60 bf01d128 00a08021 move     $s0, $a1
00006d64 bf01d12c 2404003f addiu    $a0, $zero, 0x3f
00006d68 bf01d130 0bc074b5 j        0xbf01d2d4
00006d6c bf01d134 24030020 addiu    $v1, $zero, 0x20
00006d70 bf01d138 14440055 bne      $v0, $a0, 0xbf01d290
00006d74 bf01d13c 00000000 nop      
00006d78 bf01d140 82620008 lb       $v0, 8($s3)
00006d7c bf01d144 5440000c bnel     $v0, $zero, 0xbf01d178
00006d80 bf01d148 26100001 addiu    $s0, $s0, 1
00006d84 bf01d14c 02053023 subu     $a2, $s0, $a1
00006d88 bf01d150 2cc20080 sltiu    $v0, $a2, 0x80
00006d8c bf01d154 10400166 beqz     $v0, 0xbf01d6f0
00006d90 bf01d158 2402ffff addiu    $v0, $zero, -1
00006d94 bf01d15c 0ff0ce8c jal      0xbfc33a30
00006d98 bf01d160 26640008 addiu    $a0, $s3, 8
00006d9c bf01d164 8e62008c lw       $v0, 0x8c($s3)
00006da0 bf01d168 02021023 subu     $v0, $s0, $v0
00006da4 bf01d16c 02621021 addu     $v0, $s3, $v0
00006da8 bf01d170 a0400008 sb       $zero, 8($v0)
00006dac bf01d174 26100001 addiu    $s0, $s0, 1
00006db0 bf01d178 24080020 addiu    $t0, $zero, 0x20
00006db4 bf01d17c 240a003d addiu    $t2, $zero, 0x3d
00006db8 bf01d180 24090026 addiu    $t1, $zero, 0x26
00006dbc bf01d184 92020000 lbu      $v0, ($s0)
00006dc0 bf01d188 10480056 beq      $v0, $t0, 0xbf01d2e4
00006dc4 bf01d18c 26030001 addiu    $v1, $s0, 1
00006dc8 bf01d190 86620150 lh       $v0, 0x150($s3)
00006dcc bf01d194 8e630088 lw       $v1, 0x88($s3)
00006dd0 bf01d198 24420054 addiu    $v0, $v0, 0x54
00006dd4 bf01d19c 00021080 sll      $v0, $v0, 2
00006dd8 bf01d1a0 02621021 addu     $v0, $s3, $v0
00006ddc bf01d1a4 02031823 subu     $v1, $s0, $v1
00006de0 bf01d1a8 a4430004 sh       $v1, 4($v0)
00006de4 bf01d1ac 92020000 lbu      $v0, ($s0)
00006de8 bf01d1b0 504a0006 beql     $v0, $t2, 0xbf01d1cc
00006dec bf01d1b4 86620150 lh       $v0, 0x150($s3)
00006df0 bf01d1b8 26940001 addiu    $s4, $s4, 1
00006df4 bf01d1bc 0296102a slt      $v0, $s4, $s6
00006df8 bf01d1c0 1440fffa bnez     $v0, 0xbf01d1ac
00006dfc bf01d1c4 26100001 addiu    $s0, $s0, 1
00006e00 bf01d1c8 86620150 lh       $v0, 0x150($s3)
00006e04 bf01d1cc 8e630088 lw       $v1, 0x88($s3)
00006e08 bf01d1d0 24420054 addiu    $v0, $v0, 0x54
00006e0c bf01d1d4 00021080 sll      $v0, $v0, 2
00006e10 bf01d1d8 02622021 addu     $a0, $s3, $v0
00006e14 bf01d1dc 84820004 lh       $v0, 4($a0)
00006e18 bf01d1e0 26060001 addiu    $a2, $s0, 1
00006e1c bf01d1e4 00621821 addu     $v1, $v1, $v0
00006e20 bf01d1e8 00c31823 subu     $v1, $a2, $v1
00006e24 bf01d1ec 28620100 slti     $v0, $v1, 0x100
00006e28 bf01d1f0 1040013c beqz     $v0, 0xbf01d6e4
00006e2c bf01d1f4 02803821 move     $a3, $s4
00006e30 bf01d1f8 0bc07497 j        0xbf01d25c
00006e34 bf01d1fc a0830006 sb       $v1, 6($a0)
00006e38 bf01d200 50490004 beql     $v0, $t1, 0xbf01d214
00006e3c bf01d204 86620150 lh       $v0, 0x150($s3)
00006e40 bf01d208 54480013 bnel     $v0, $t0, 0xbf01d258
00006e44 bf01d20c 24c60001 addiu    $a2, $a2, 1
00006e48 bf01d210 86620150 lh       $v0, 0x150($s3)
00006e4c bf01d214 8e640088 lw       $a0, 0x88($s3)
00006e50 bf01d218 24420054 addiu    $v0, $v0, 0x54
00006e54 bf01d21c 00021080 sll      $v0, $v0, 2
00006e58 bf01d220 02622821 addu     $a1, $s3, $v0
00006e5c bf01d224 84a30004 lh       $v1, 4($a1)
00006e60 bf01d228 90a20006 lbu      $v0, 6($a1)
00006e64 bf01d22c 00431021 addu     $v0, $v0, $v1
00006e68 bf01d230 00822021 addu     $a0, $a0, $v0
00006e6c bf01d234 00c41823 subu     $v1, $a2, $a0
00006e70 bf01d238 28620100 slti     $v0, $v1, 0x100
00006e74 bf01d23c 10400129 beqz     $v0, 0xbf01d6e4
00006e78 bf01d240 00c08021 move     $s0, $a2
00006e7c bf01d244 a0a30007 sb       $v1, 7($a1)
00006e80 bf01d248 96620150 lhu      $v0, 0x150($s3)
00006e84 bf01d24c 24420001 addiu    $v0, $v0, 1
00006e88 bf01d250 0bc0749b j        0xbf01d26c
00006e8c bf01d254 a6620150 sh       $v0, 0x150($s3)
00006e90 bf01d258 24e70001 addiu    $a3, $a3, 1
00006e94 bf01d25c 00f6102a slt      $v0, $a3, $s6
00006e98 bf01d260 5440ffe7 bnel     $v0, $zero, 0xbf01d200
00006e9c bf01d264 90c20000 lbu      $v0, ($a2)
00006ea0 bf01d268 00c08021 move     $s0, $a2
00006ea4 bf01d26c 90c20000 lbu      $v0, ($a2)
00006ea8 bf01d270 1048001b beq      $v0, $t0, 0xbf01d2e0
00006eac bf01d274 00e0a021 move     $s4, $a3
00006eb0 bf01d278 24f40001 addiu    $s4, $a3, 1
00006eb4 bf01d27c 0296102a slt      $v0, $s4, $s6
00006eb8 bf01d280 1440ffc0 bnez     $v0, 0xbf01d184
00006ebc bf01d284 24d00001 addiu    $s0, $a2, 1
00006ec0 bf01d288 0bc074b9 j        0xbf01d2e4
00006ec4 bf01d28c 26030001 addiu    $v1, $s0, 1
00006ec8 bf01d290 5443000f bnel     $v0, $v1, 0xbf01d2d0
00006ecc bf01d294 26100001 addiu    $s0, $s0, 1
00006ed0 bf01d298 82620008 lb       $v0, 8($s3)
00006ed4 bf01d29c 54400011 bnel     $v0, $zero, 0xbf01d2e4
00006ed8 bf01d2a0 26030001 addiu    $v1, $s0, 1
00006edc bf01d2a4 02053023 subu     $a2, $s0, $a1
00006ee0 bf01d2a8 2cc20080 sltiu    $v0, $a2, 0x80
00006ee4 bf01d2ac 10400110 beqz     $v0, 0xbf01d6f0
00006ee8 bf01d2b0 2402ffff addiu    $v0, $zero, -1
00006eec bf01d2b4 0ff0ce8c jal      0xbfc33a30
00006ef0 bf01d2b8 26640008 addiu    $a0, $s3, 8
00006ef4 bf01d2bc 8e62008c lw       $v0, 0x8c($s3)
00006ef8 bf01d2c0 02021023 subu     $v0, $s0, $v0
00006efc bf01d2c4 02621021 addu     $v0, $s3, $v0
00006f00 bf01d2c8 0bc074b8 j        0xbf01d2e0
00006f04 bf01d2cc a0400008 sb       $zero, 8($v0)
00006f08 bf01d2d0 26940001 addiu    $s4, $s4, 1
00006f0c bf01d2d4 0296102a slt      $v0, $s4, $s6
00006f10 bf01d2d8 5440ff97 bnel     $v0, $zero, 0xbf01d138
00006f14 bf01d2dc 92020000 lbu      $v0, ($s0)
00006f18 bf01d2e0 26030001 addiu    $v1, $s0, 1
00006f1c bf01d2e4 ae630090 sw       $v1, 0x90($s3)
00006f20 bf01d2e8 0bc074c0 j        0xbf01d300
00006f24 bf01d2ec 2404000d addiu    $a0, $zero, 0xd
00006f28 bf01d2f0 10440007 beq      $v0, $a0, 0xbf01d310
00006f2c bf01d2f4 24700001 addiu    $s0, $v1, 1
00006f30 bf01d2f8 24630001 addiu    $v1, $v1, 1
00006f34 bf01d2fc 26940001 addiu    $s4, $s4, 1
00006f38 bf01d300 0296102a slt      $v0, $s4, $s6
00006f3c bf01d304 5440fffa bnel     $v0, $zero, 0xbf01d2f0
00006f40 bf01d308 90620000 lbu      $v0, ($v1)
00006f44 bf01d30c 24700001 addiu    $s0, $v1, 1
00006f48 bf01d310 3c02bfce lui      $v0, 0xbfce
00006f4c bf01d314 ae700094 sw       $s0, 0x94($s3)
00006f50 bf01d318 0bc074ce j        0xbf01d338
00006f54 bf01d31c 2451b6d0 addiu    $s1, $v0, -0x4930
00006f58 bf01d320 0ff0ce98 jal      0xbfc33a60
00006f5c bf01d324 00000000 nop      
00006f60 bf01d328 10400009 beqz     $v0, 0xbf01d350
00006f64 bf01d32c 26020001 addiu    $v0, $s0, 1
00006f68 bf01d330 26100001 addiu    $s0, $s0, 1
00006f6c bf01d334 26940001 addiu    $s4, $s4, 1
00006f70 bf01d338 0296102a slt      $v0, $s4, $s6
00006f74 bf01d33c 2604fffd addiu    $a0, $s0, -3
00006f78 bf01d340 02202821 move     $a1, $s1
00006f7c bf01d344 1440fff6 bnez     $v0, 0xbf01d320
00006f80 bf01d348 24060004 addiu    $a2, $zero, 4
00006f84 bf01d34c 26020001 addiu    $v0, $s0, 1
00006f88 bf01d350 ae620098 sw       $v0, 0x98($s3)
00006f8c bf01d354 3c02bfce lui      $v0, 0xbfce
00006f90 bf01d358 a26000ec sb       $zero, 0xec($s3)
00006f94 bf01d35c ae60009c sw       $zero, 0x9c($s3)
00006f98 bf01d360 ae6000a0 sw       $zero, 0xa0($s3)
00006f9c bf01d364 ae6000e4 sw       $zero, 0xe4($s3)
00006fa0 bf01d368 ae6000e8 sw       $zero, 0xe8($s3)
00006fa4 bf01d36c 245ed8f8 addiu    $fp, $v0, -0x2708
00006fa8 bf01d370 8e710094 lw       $s1, 0x94($s3)
00006fac bf01d374 267200ec addiu    $s2, $s3, 0xec
00006fb0 bf01d378 2410000a addiu    $s0, $zero, 0xa
00006fb4 bf01d37c 0bc07525 j        0xbf01d494
00006fb8 bf01d380 2415000d addiu    $s5, $zero, 0xd
00006fbc bf01d384 02202021 move     $a0, $s1
00006fc0 bf01d388 24a5e608 addiu    $a1, $a1, -0x19f8
00006fc4 bf01d38c 0ff0ce98 jal      0xbfc33a60
00006fc8 bf01d390 24060008 addiu    $a2, $zero, 8
00006fcc bf01d394 1440000f bnez     $v0, 0xbf01d3d4
00006fd0 bf01d398 26250008 addiu    $a1, $s1, 8
00006fd4 bf01d39c ae65009c sw       $a1, 0x9c($s3)
00006fd8 bf01d3a0 00a08821 move     $s1, $a1
00006fdc bf01d3a4 92220000 lbu      $v0, ($s1)
00006fe0 bf01d3a8 5450fffe bnel     $v0, $s0, 0xbf01d3a4
00006fe4 bf01d3ac 26310001 addiu    $s1, $s1, 1
00006fe8 bf01d3b0 00053027 nor      $a2, $zero, $a1
00006fec bf01d3b4 02263021 addu     $a2, $s1, $a2
00006ff0 bf01d3b8 0ff0ce8c jal      0xbfc33a30
00006ff4 bf01d3bc 02402021 move     $a0, $s2
00006ff8 bf01d3c0 8e63009c lw       $v1, 0x9c($s3)
00006ffc bf01d3c4 02711021 addu     $v0, $s3, $s1
00007000 bf01d3c8 00431023 subu     $v0, $v0, $v1
00007004 bf01d3cc 0bc07524 j        0xbf01d490
00007008 bf01d3d0 a04000eb sb       $zero, 0xeb($v0)
0000700c bf01d3d4 3c05bfce lui      $a1, 0xbfce
00007010 bf01d3d8 02202021 move     $a0, $s1
00007014 bf01d3dc 24a5d8c8 addiu    $a1, $a1, -0x2738
00007018 bf01d3e0 0ff0ce98 jal      0xbfc33a60
0000701c bf01d3e4 2406000e addiu    $a2, $zero, 0xe
00007020 bf01d3e8 14400008 bnez     $v0, 0xbf01d40c
00007024 bf01d3ec 3c05bfce lui      $a1, 0xbfce
00007028 bf01d3f0 2631000e addiu    $s1, $s1, 0xe
0000702c bf01d3f4 ae7100a0 sw       $s1, 0xa0($s3)
00007030 bf01d3f8 92220000 lbu      $v0, ($s1)
00007034 bf01d3fc 1450fffe bne      $v0, $s0, 0xbf01d3f8
00007038 bf01d400 26310001 addiu    $s1, $s1, 1
0000703c bf01d404 0bc07526 j        0xbf01d498
00007040 bf01d408 8e620098 lw       $v0, 0x98($s3)
00007044 bf01d40c 02202021 move     $a0, $s1
00007048 bf01d410 24a5d8d8 addiu    $a1, $a1, -0x2728
0000704c bf01d414 0ff0ce98 jal      0xbfc33a60
00007050 bf01d418 24060010 addiu    $a2, $zero, 0x10
00007054 bf01d41c 14400012 bnez     $v0, 0xbf01d468
00007058 bf01d420 02202021 move     $a0, $s1
0000705c bf01d424 0bc07515 j        0xbf01d454
00007060 bf01d428 26310010 addiu    $s1, $s1, 0x10
00007064 bf01d42c 50550009 beql     $v0, $s5, 0xbf01d454
00007068 bf01d430 26310001 addiu    $s1, $s1, 1
0000706c bf01d434 8e6200e4 lw       $v0, 0xe4($s3)
00007070 bf01d438 70501002 mul      $v0, $v0, $s0
00007074 bf01d43c ae6200e4 sw       $v0, 0xe4($s3)
00007078 bf01d440 92230000 lbu      $v1, ($s1)
0000707c bf01d444 00431021 addu     $v0, $v0, $v1
00007080 bf01d448 2442ffd0 addiu    $v0, $v0, -0x30
00007084 bf01d44c ae6200e4 sw       $v0, 0xe4($s3)
00007088 bf01d450 26310001 addiu    $s1, $s1, 1
0000708c bf01d454 92220000 lbu      $v0, ($s1)
00007090 bf01d458 1450fff4 bne      $v0, $s0, 0xbf01d42c
00007094 bf01d45c 00000000 nop      
00007098 bf01d460 0bc07525 j        0xbf01d494
0000709c bf01d464 26310001 addiu    $s1, $s1, 1
000070a0 bf01d468 03c02821 move     $a1, $fp
000070a4 bf01d46c 0ff0ce98 jal      0xbfc33a60
000070a8 bf01d470 24060013 addiu    $a2, $zero, 0x13
000070ac bf01d474 54400007 bnel     $v0, $zero, 0xbf01d494
000070b0 bf01d478 26310001 addiu    $s1, $s1, 1
000070b4 bf01d47c 26310013 addiu    $s1, $s1, 0x13
000070b8 bf01d480 ae7100e8 sw       $s1, 0xe8($s3)
000070bc bf01d484 92220000 lbu      $v0, ($s1)
000070c0 bf01d488 5450fffe bnel     $v0, $s0, 0xbf01d484
000070c4 bf01d48c 26310001 addiu    $s1, $s1, 1
000070c8 bf01d490 26310001 addiu    $s1, $s1, 1
000070cc bf01d494 8e620098 lw       $v0, 0x98($s3)
000070d0 bf01d498 0222102b sltu     $v0, $s1, $v0
000070d4 bf01d49c 1440ffb9 bnez     $v0, 0xbf01d384
000070d8 bf01d4a0 3c05bfce lui      $a1, 0xbfce
000070dc bf01d4a4 8e6400a0 lw       $a0, 0xa0($s3)
000070e0 bf01d4a8 ae60029c sw       $zero, 0x29c($s3)
000070e4 bf01d4ac 1080003b beqz     $a0, 0xbf01d59c
000070e8 bf01d4b0 ae6002a0 sw       $zero, 0x2a0($s3)
000070ec bf01d4b4 3c05bfce lui      $a1, 0xbfce
000070f0 bf01d4b8 24a5d90c addiu    $a1, $a1, -0x26f4
000070f4 bf01d4bc 0ff0ce98 jal      0xbfc33a60
000070f8 bf01d4c0 24060009 addiu    $a2, $zero, 9
000070fc bf01d4c4 54400036 bnel     $v0, $zero, 0xbf01d5a0
00007100 bf01d4c8 8e630004 lw       $v1, 4($s3)
00007104 bf01d4cc 8e6400a0 lw       $a0, 0xa0($s3)
00007108 bf01d4d0 8e660098 lw       $a2, 0x98($s3)
0000710c bf01d4d4 3c05bfce lui      $a1, 0xbfce
00007110 bf01d4d8 00c43023 subu     $a2, $a2, $a0
00007114 bf01d4dc 0ff0b074 jal      0xbfc2c1d0
00007118 bf01d4e0 24a5d720 addiu    $a1, $a1, -0x28e0
0000711c bf01d4e4 8e6400a0 lw       $a0, 0xa0($s3)
00007120 bf01d4e8 8e660098 lw       $a2, 0x98($s3)
00007124 bf01d4ec 3c15bfce lui      $s5, 0xbfce
00007128 bf01d4f0 00408021 move     $s0, $v0
0000712c bf01d4f4 00c43023 subu     $a2, $a2, $a0
00007130 bf01d4f8 0ff0b074 jal      0xbfc2c1d0
00007134 bf01d4fc 26a5d918 addiu    $a1, $s5, -0x26e8
00007138 bf01d500 2610fff7 addiu    $s0, $s0, -9
0000713c bf01d504 02029023 subu     $s2, $s0, $v0
00007140 bf01d508 2a420040 slti     $v0, $s2, 0x40
00007144 bf01d50c 50400024 beql     $v0, $zero, 0xbf01d5a0
00007148 bf01d510 8e630004 lw       $v1, 4($s3)
0000714c bf01d514 8e6400a0 lw       $a0, 0xa0($s3)
00007150 bf01d518 0ff0b0c9 jal      0xbfc2c324
00007154 bf01d51c 26a5d918 addiu    $a1, $s5, -0x26e8
00007158 bf01d520 267000a4 addiu    $s0, $s3, 0xa4
0000715c bf01d524 02403021 move     $a2, $s2
00007160 bf01d528 24450009 addiu    $a1, $v0, 9
00007164 bf01d52c 0ff0ce8c jal      0xbfc33a30
00007168 bf01d530 02002021 move     $a0, $s0
0000716c bf01d534 8e640098 lw       $a0, 0x98($s3)
00007170 bf01d538 02721021 addu     $v0, $s3, $s2
00007174 bf01d53c 02f69021 addu     $s2, $s7, $s6
00007178 bf01d540 a04000a4 sb       $zero, 0xa4($v0)
0000717c bf01d544 02002821 move     $a1, $s0
00007180 bf01d548 0ff0b074 jal      0xbfc2c1d0
00007184 bf01d54c 02443023 subu     $a2, $s2, $a0
00007188 bf01d550 50400013 beql     $v0, $zero, 0xbf01d5a0
0000718c bf01d554 8e630004 lw       $v1, 4($s3)
00007190 bf01d558 8e640098 lw       $a0, 0x98($s3)
00007194 bf01d55c 3c05bfce lui      $a1, 0xbfce
00007198 bf01d560 02443023 subu     $a2, $s2, $a0
0000719c bf01d564 0ff0b074 jal      0xbfc2c1d0
000071a0 bf01d568 24a5b6d0 addiu    $a1, $a1, -0x4930
000071a4 bf01d56c 1040000b beqz     $v0, 0xbf01d59c
000071a8 bf01d570 00402021 move     $a0, $v0
000071ac bf01d574 8e6200e4 lw       $v0, 0xe4($s3)
000071b0 bf01d578 8e630098 lw       $v1, 0x98($s3)
000071b4 bf01d57c 24840004 addiu    $a0, $a0, 4
000071b8 bf01d580 00621821 addu     $v1, $v1, $v0
000071bc bf01d584 00641823 subu     $v1, $v1, $a0
000071c0 bf01d588 02441023 subu     $v0, $s2, $a0
000071c4 bf01d58c ae6202a0 sw       $v0, 0x2a0($s3)
000071c8 bf01d590 ae6302a8 sw       $v1, 0x2a8($s3)
000071cc bf01d594 ae64029c sw       $a0, 0x29c($s3)
000071d0 bf01d598 ae6002a4 sw       $zero, 0x2a4($s3)
000071d4 bf01d59c 8e630004 lw       $v1, 4($s3)
000071d8 bf01d5a0 24020002 addiu    $v0, $zero, 2
000071dc bf01d5a4 14620052 bne      $v1, $v0, 0xbf01d6f0
000071e0 bf01d5a8 00001021 move     $v0, $zero
000071e4 bf01d5ac 3c05bfce lui      $a1, 0xbfce
000071e8 bf01d5b0 8e6400a0 lw       $a0, 0xa0($s3)
000071ec bf01d5b4 24a5d90c addiu    $a1, $a1, -0x26f4
000071f0 bf01d5b8 0ff0ce98 jal      0xbfc33a60
000071f4 bf01d5bc 24060009 addiu    $a2, $zero, 9
000071f8 bf01d5c0 14400041 bnez     $v0, 0xbf01d6c8
000071fc bf01d5c4 02f62821 addu     $a1, $s7, $s6
00007200 bf01d5c8 0bc075bc j        0xbf01d6f0
00007204 bf01d5cc 00001021 move     $v0, $zero
00007208 bf01d5d0 10400047 beqz     $v0, 0xbf01d6f0
0000720c bf01d5d4 00001021 move     $v0, $zero
00007210 bf01d5d8 86620150 lh       $v0, 0x150($s3)
00007214 bf01d5dc 8e630088 lw       $v1, 0x88($s3)
00007218 bf01d5e0 24420054 addiu    $v0, $v0, 0x54
0000721c bf01d5e4 00021080 sll      $v0, $v0, 2
00007220 bf01d5e8 02621021 addu     $v0, $s3, $v0
00007224 bf01d5ec 02231823 subu     $v1, $s1, $v1
00007228 bf01d5f0 a4430004 sh       $v1, 4($v0)
0000722c bf01d5f4 92220000 lbu      $v0, ($s1)
00007230 bf01d5f8 50490006 beql     $v0, $t1, 0xbf01d614
00007234 bf01d5fc 86620150 lh       $v0, 0x150($s3)
00007238 bf01d600 26940001 addiu    $s4, $s4, 1
0000723c bf01d604 0296102a slt      $v0, $s4, $s6
00007240 bf01d608 1440fffa bnez     $v0, 0xbf01d5f4
00007244 bf01d60c 26310001 addiu    $s1, $s1, 1
00007248 bf01d610 86620150 lh       $v0, 0x150($s3)
0000724c bf01d614 8e630088 lw       $v1, 0x88($s3)
00007250 bf01d618 24420054 addiu    $v0, $v0, 0x54
00007254 bf01d61c 00021080 sll      $v0, $v0, 2
00007258 bf01d620 02622021 addu     $a0, $s3, $v0
0000725c bf01d624 84820004 lh       $v0, 4($a0)
00007260 bf01d628 26260001 addiu    $a2, $s1, 1
00007264 bf01d62c 00621821 addu     $v1, $v1, $v0
00007268 bf01d630 00c31823 subu     $v1, $a2, $v1
0000726c bf01d634 28620100 slti     $v0, $v1, 0x100
00007270 bf01d638 1040002d beqz     $v0, 0xbf01d6f0
00007274 bf01d63c 2402ffff addiu    $v0, $zero, -1
00007278 bf01d640 0bc075aa j        0xbf01d6a8
0000727c bf01d644 a0830006 sb       $v1, 6($a0)
00007280 bf01d648 90c20000 lbu      $v0, ($a2)
00007284 bf01d64c 50480004 beql     $v0, $t0, 0xbf01d660
00007288 bf01d650 86620150 lh       $v0, 0x150($s3)
0000728c bf01d654 54600013 bnel     $v1, $zero, 0xbf01d6a4
00007290 bf01d658 24c60001 addiu    $a2, $a2, 1
00007294 bf01d65c 86620150 lh       $v0, 0x150($s3)
00007298 bf01d660 8e640088 lw       $a0, 0x88($s3)
0000729c bf01d664 24420054 addiu    $v0, $v0, 0x54
000072a0 bf01d668 00021080 sll      $v0, $v0, 2
000072a4 bf01d66c 02623821 addu     $a3, $s3, $v0
000072a8 bf01d670 84e30004 lh       $v1, 4($a3)
000072ac bf01d674 90e20006 lbu      $v0, 6($a3)
000072b0 bf01d678 00431021 addu     $v0, $v0, $v1
000072b4 bf01d67c 00822021 addu     $a0, $a0, $v0
000072b8 bf01d680 00c41823 subu     $v1, $a2, $a0
000072bc bf01d684 28620100 slti     $v0, $v1, 0x100
000072c0 bf01d688 10400019 beqz     $v0, 0xbf01d6f0
000072c4 bf01d68c 2402ffff addiu    $v0, $zero, -1
000072c8 bf01d690 a0e30007 sb       $v1, 7($a3)
000072cc bf01d694 96620150 lhu      $v0, 0x150($s3)
000072d0 bf01d698 24420001 addiu    $v0, $v0, 1
000072d4 bf01d69c 0bc075ad j        0xbf01d6b4
000072d8 bf01d6a0 a6620150 sh       $v0, 0x150($s3)
000072dc bf01d6a4 26940001 addiu    $s4, $s4, 1
000072e0 bf01d6a8 0296102a slt      $v0, $s4, $s6
000072e4 bf01d6ac 1440ffe6 bnez     $v0, 0xbf01d648
000072e8 bf01d6b0 00c5182b sltu     $v1, $a2, $a1
000072ec bf01d6b4 00c5102b sltu     $v0, $a2, $a1
000072f0 bf01d6b8 1040000c beqz     $v0, 0xbf01d6ec
000072f4 bf01d6bc 24d10001 addiu    $s1, $a2, 1
000072f8 bf01d6c0 0bc075b4 j        0xbf01d6d0
000072fc bf01d6c4 26940001 addiu    $s4, $s4, 1
00007300 bf01d6c8 2409003d addiu    $t1, $zero, 0x3d
00007304 bf01d6cc 24080026 addiu    $t0, $zero, 0x26
00007308 bf01d6d0 0296102a slt      $v0, $s4, $s6
0000730c bf01d6d4 5440ffbe bnel     $v0, $zero, 0xbf01d5d0
00007310 bf01d6d8 92220000 lbu      $v0, ($s1)
00007314 bf01d6dc 0bc075bc j        0xbf01d6f0
00007318 bf01d6e0 00001021 move     $v0, $zero
0000731c bf01d6e4 0bc075bc j        0xbf01d6f0
00007320 bf01d6e8 2402ffff addiu    $v0, $zero, -1
00007324 bf01d6ec 00001021 move     $v0, $zero
00007328 bf01d6f0 8fbf0034 lw       $ra, 0x34($sp)
0000732c bf01d6f4 8fbe0030 lw       $fp, 0x30($sp)
00007330 bf01d6f8 8fb7002c lw       $s7, 0x2c($sp)
00007334 bf01d6fc 8fb60028 lw       $s6, 0x28($sp)
00007338 bf01d700 8fb50024 lw       $s5, 0x24($sp)
0000733c bf01d704 8fb40020 lw       $s4, 0x20($sp)
00007340 bf01d708 8fb3001c lw       $s3, 0x1c($sp)
00007344 bf01d70c 8fb20018 lw       $s2, 0x18($sp)
00007348 bf01d710 8fb10014 lw       $s1, 0x14($sp)
0000734c bf01d714 8fb00010 lw       $s0, 0x10($sp)
00007350 bf01d718 03e00008 jr       $ra
00007354 bf01d71c 27bd0038 addiu    $sp, $sp, 0x38
00007358 bf01d720 27bdffc8 addiu    $sp, $sp, -0x38
0000735c bf01d724 afbf0034 sw       $ra, 0x34($sp)
00007360 bf01d728 afb70030 sw       $s7, 0x30($sp)
00007364 bf01d72c afb6002c sw       $s6, 0x2c($sp)
00007368 bf01d730 afb50028 sw       $s5, 0x28($sp)
0000736c bf01d734 afb40024 sw       $s4, 0x24($sp)
00007370 bf01d738 afb30020 sw       $s3, 0x20($sp)
00007374 bf01d73c afb2001c sw       $s2, 0x1c($sp)
00007378 bf01d740 afb10018 sw       $s1, 0x18($sp)
0000737c bf01d744 afb00014 sw       $s0, 0x14($sp)
00007380 bf01d748 00a0a821 move     $s5, $a1
00007384 bf01d74c 00c09821 move     $s3, $a2
00007388 bf01d750 0ff0e22d jal      0xbfc388b4
0000738c bf01d754 0080b021 move     $s6, $a0
00007390 bf01d758 00408021 move     $s0, $v0
00007394 bf01d75c 3c02bf01 lui      $v0, 0xbf01
00007398 bf01d760 8c420f48 lw       $v0, 0xf48($v0)
0000739c bf01d764 12c2001b beq      $s6, $v0, 0xbf01d7d4
000073a0 bf01d768 3c03bf01 lui      $v1, 0xbf01
000073a4 bf01d76c 02002021 move     $a0, $s0
000073a8 bf01d770 02a02821 move     $a1, $s5
000073ac bf01d774 0fc073da jal      0xbf01cf68
000073b0 bf01d778 02603021 move     $a2, $s3
000073b4 bf01d77c 14400011 bnez     $v0, 0xbf01d7c4
000073b8 bf01d780 00401821 move     $v1, $v0
000073bc bf01d784 26110004 addiu    $s1, $s0, 4
000073c0 bf01d788 ae160004 sw       $s6, 4($s0)
000073c4 bf01d78c 02a02821 move     $a1, $s5
000073c8 bf01d790 02603021 move     $a2, $s3
000073cc bf01d794 0fc07417 jal      0xbf01d05c
000073d0 bf01d798 02202021 move     $a0, $s1
000073d4 bf01d79c 5440007f bnel     $v0, $zero, 0xbf01d99c
000073d8 bf01d7a0 02c02021 move     $a0, $s6
000073dc bf01d7a4 3c02bf01 lui      $v0, 0xbf01
000073e0 bf01d7a8 8c421654 lw       $v0, 0x1654($v0)
000073e4 bf01d7ac 10400087 beqz     $v0, 0xbf01d9cc
000073e8 bf01d7b0 8fbf0034 lw       $ra, 0x34($sp)
000073ec bf01d7b4 0040f809 jalr     $v0
000073f0 bf01d7b8 02202021 move     $a0, $s1
000073f4 bf01d7bc 0bc07667 j        0xbf01d99c
000073f8 bf01d7c0 02c02021 move     $a0, $s6
000073fc bf01d7c4 2402ffff addiu    $v0, $zero, -1
00007400 bf01d7c8 10620074 beq      $v1, $v0, 0xbf01d99c
00007404 bf01d7cc 02c02021 move     $a0, $s6
00007408 bf01d7d0 3c03bf01 lui      $v1, 0xbf01
0000740c bf01d7d4 8c620f48 lw       $v0, 0xf48($v1)
00007410 bf01d7d8 04410006 bgez     $v0, 0xbf01d7f4
00007414 bf01d7dc 00000000 nop      
00007418 bf01d7e0 8e020000 lw       $v0, ($s0)
0000741c bf01d7e4 ac620f48 sw       $v0, 0xf48($v1)
00007420 bf01d7e8 3c02bf01 lui      $v0, 0xbf01
00007424 bf01d7ec 0bc07600 j        0xbf01d800
00007428 bf01d7f0 ac400f44 sw       $zero, 0xf44($v0)
0000742c bf01d7f4 14560069 bne      $v0, $s6, 0xbf01d99c
00007430 bf01d7f8 02c02021 move     $a0, $s6
00007434 bf01d7fc 3c02bf01 lui      $v0, 0xbf01
00007438 bf01d800 8c430f44 lw       $v1, 0xf44($v0)
0000743c bf01d804 02631021 addu     $v0, $s3, $v1
00007440 bf01d808 2c420601 sltiu    $v0, $v0, 0x601
00007444 bf01d80c 14400003 bnez     $v0, 0xbf01d81c
00007448 bf01d810 02608821 move     $s1, $s3
0000744c bf01d814 24020600 addiu    $v0, $zero, 0x600
00007450 bf01d818 00438823 subu     $s1, $v0, $v1
00007454 bf01d81c 3c02bf01 lui      $v0, 0xbf01
00007458 bf01d820 24540940 addiu    $s4, $v0, 0x940
0000745c bf01d824 02832021 addu     $a0, $s4, $v1
00007460 bf01d828 02a02821 move     $a1, $s5
00007464 bf01d82c 02203021 move     $a2, $s1
00007468 bf01d830 0ff0ce8c jal      0xbfc33a30
0000746c bf01d834 3c12bf01 lui      $s2, 0xbf01
00007470 bf01d838 8e420f44 lw       $v0, 0xf44($s2)
00007474 bf01d83c 02002021 move     $a0, $s0
00007478 bf01d840 02221021 addu     $v0, $s1, $v0
0000747c bf01d844 00541821 addu     $v1, $v0, $s4
00007480 bf01d848 00403021 move     $a2, $v0
00007484 bf01d84c 02802821 move     $a1, $s4
00007488 bf01d850 a0600000 sb       $zero, ($v1)
0000748c bf01d854 ae420f44 sw       $v0, 0xf44($s2)
00007490 bf01d858 0fc073da jal      0xbf01cf68
00007494 bf01d85c 2417ffff addiu    $s7, $zero, -1
00007498 bf01d860 1057004e beq      $v0, $s7, 0xbf01d99c
0000749c bf01d864 02c02021 move     $a0, $s6
000074a0 bf01d868 14400012 bnez     $v0, 0xbf01d8b4
000074a4 bf01d86c 8e430f44 lw       $v1, 0xf44($s2)
000074a8 bf01d870 26110004 addiu    $s1, $s0, 4
000074ac bf01d874 8e460f44 lw       $a2, 0xf44($s2)
000074b0 bf01d878 02802821 move     $a1, $s4
000074b4 bf01d87c ae160004 sw       $s6, 4($s0)
000074b8 bf01d880 0fc07417 jal      0xbf01d05c
000074bc bf01d884 02202021 move     $a0, $s1
000074c0 bf01d888 54400044 bnel     $v0, $zero, 0xbf01d99c
000074c4 bf01d88c 02c02021 move     $a0, $s6
000074c8 bf01d890 3c02bf01 lui      $v0, 0xbf01
000074cc bf01d894 8c421654 lw       $v0, 0x1654($v0)
000074d0 bf01d898 1040004c beqz     $v0, 0xbf01d9cc
000074d4 bf01d89c 8fbf0034 lw       $ra, 0x34($sp)
000074d8 bf01d8a0 0040f809 jalr     $v0
000074dc bf01d8a4 02202021 move     $a0, $s1
000074e0 bf01d8a8 3c02bf01 lui      $v0, 0xbf01
000074e4 bf01d8ac 0bc07666 j        0xbf01d998
000074e8 bf01d8b0 ac570f48 sw       $s7, 0xf48($v0)
000074ec bf01d8b4 24020600 addiu    $v0, $zero, 0x600
000074f0 bf01d8b8 14620044 bne      $v1, $v0, 0xbf01d9cc
000074f4 bf01d8bc 8fbf0034 lw       $ra, 0x34($sp)
000074f8 bf01d8c0 8e0302b0 lw       $v1, 0x2b0($s0)
000074fc bf01d8c4 0461001f bgez     $v1, 0xbf01d944
