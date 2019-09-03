(define (cont-frac Ni Di k)
  (define (iter cur result)
    (if (= cur 0)
        result
        (iter
          (- cur 1)
          (/ (Ni cur)
             (+ (Di cur) result)))))
  (iter k 0))

(define (tan-cf x k)
  (cont-frac
    (lambda (i)
      (if (= i 1)
          x
          (- (* x x))))
    (lambda (i)
      (- (* 2 i) 1))
    k))
