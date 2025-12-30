; --- DATA SECTION ---
	x	DW	?
	y	DW	?
	pi	DB	?

; --- CODE SECTION ---
FUNC_main:
	MOV	10, , x
	MOV	20, , y
	MOV	3.14, , pi
	ADD	x, y, t1
	ASTORE	t1, 0, arr
	ALOAD	arr, 0, t2
	PRINT	t2, , 
	LT	x, y, t3
	JPF	t3, L1, 
	PRINT	x, , 
	JMP	L2, , 
L1:
	PRINT	y, , 
L2:
L3:
	GT	x, 0, t4
	JPF	t4, L4, 
	SUB	x, 1, t5
	MOV	t5, , x
	EQ	x, 5, t6
	JPF	t6, L5, 
	JMP	L6, , 
L5:
L6:
	JMP	L3, , 
L4:
	RET	, , 