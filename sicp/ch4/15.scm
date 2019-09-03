; Given a one-argument procedure p and an object a,
; p is said to “halt” on a if evaluating the expression (p a)
; returns a value(as opposed to terminating with an error message or running forever).
; Show that it is impossible to write a procedure halts? that
; correctly determines whether p halts on a for any procedure p and object a.
; Use the following reasoning: If you had such a procedure halts?,
; you could implement the following program:

(define (run-forever) (run-forever))
(define (try p)
  (if (halts? p p)
      (run-forever)
      'halted))

; Now consider evaluating the expression (try try)
; and show that any possible outcome (either halting or running forever)
; violates the intended behavior of halts?.

; =========================

; suppose these exists a procedure halts? that can
; test whether a procedure p will halt or not
; for a given input a,
;
; then when evaluating the expression (try try):
;
; if (halts? try try) evaluates to true (which means try will halt),
; then we will fall into the consequence and call run-forever
; (which means try will not halt), this is a contradiction;
;
; or (halts? try try) evaluates to false (which means try will not halt),
; then we will fall into the alternative and get 'halted as return value,
; (which means try will halt), this is also a contradiction.
;
; contradiction obtained for both case, suppose can not hold.
; i.e., such procedure halt? does not exist
; if it want to handle any procedure with any object
; as its input.
