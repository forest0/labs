(define (an-integer-between low high)
  (require (<= low high))
  (amb low (an-interger-between (+ low 1) high)))
