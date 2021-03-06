(define (product term a next b)
  (define (product-iter cur result)
    (if (> cur b)
        result
        (product-iter
          (next cur)
          (* result (term cur)))))
  (product-iter a 1))

(define (factorial n)
  (define (term a) a)
  (define (next a) (+ a 1))
  (product term 1 next n))

(define (pi n)
  (define (term-numerator k)
    (cond ((= k 1) 2)
          ((even? k) (+ k 2))
          (else (+ k 1))))
  (define (term-denominator k)
    (if (even? k)
        (+ k 1)
        (+ k 2)))
  (define (next a)
    (+ a 1))
  (* (exact->inexact 4)
     (/ (product term-numerator 1 next n)
        (product term-denominator 1 next n))))
