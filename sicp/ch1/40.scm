(define (cubic a b c)
  (lambda (x)
    (+ (* x x x)
       (* a (square x))
       (* b x)
       c)))
