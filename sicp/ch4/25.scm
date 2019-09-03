(define (my-unless condition usual-value exceptional-value)
  (if condition
      exceptional-value
      usual-value))

(define (factorial n)
  (my-unless (= n 1)
    (* n (factorial (- n 1)))
    1))

; in applicative-order
(factorial 3)
(my-unless #f
           (* n (factorial 2))
           1)

(factorial 2)
(my-unless #f
           (* n (factorial 1))
           1)

(factorial 1)
(my-unless #t
           (* 1 (factorial 0))
           1)

(factorial 0)
(my-unless #f
           (* 0 (factorial -1))
           1)
; ...
; never stop

; ======================

; in normal-order
(factorial 3)
(my-unless #f
           (* 3 (factorial 2)))

(factorial 2)
(my-unless #f
           (* 2 (factorial 1)))

(factorial 1)
(my-unless #f
           1)
; then return
