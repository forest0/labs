; O(log)
(define (expmod base exp m)
  (cond ((= exp 0) 1)
        ((even? exp)
         (remainder
           (square (expmod base (/ exp 2) m))
           m))
        (else
          (remainder
            (* base (expmod base (- exp 1) m))
            m))))

; O(n)
; prime? return true is NOT a guarantee
; that n is prime
; so the following procedure is useless
(define (prime? n)
  (define (try-it a)
    (= (expmod a n n) a))
  (define (prime-iter n cur)
    (cond ((= cur 1) true)
          ((try-it cur) (prime-iter n (- cur 1)))
          (else false)))
  (if (prime-iter n (- n 1))
      "may be a prime"
      "not prime"))
