(define (cont-frac Ni Di k)
  (define (iter cur result)
    (if (= cur 0)
        result
        (iter
          (- cur 1)
          (/ (Ni cur)
             (+ (Di cur) result)))))
  (iter k 0))
