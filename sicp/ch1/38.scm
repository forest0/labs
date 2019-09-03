(define (cont-frac Ni Di k)
  (define (iter cur result)
    (if (= cur 0)
        result
        (iter
          (- cur 1)
          (/ (Ni cur)
             (+ (Di cur) result)))))
  (iter k 0))

(+ 2
   (cont-frac
     (lambda (i) 1.0)
     (lambda (i)
       (if (= 2 (remainder i 3))
           (/ (* 2 (+ i 1)) 3)
           1))
     10))
