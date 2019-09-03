(define (accumulate combiner null-value term a next b)
  (define (accumulate-iter cur result)
    (if (> cur b)
        result
        (accumulate-iter
          (next cur)
          (combiner
            (term cur)
            result))))
  (accumulate-iter a null-value))

(define (sum term a next b)
  (accumulate + 0 term a next b))

(define (product term a next b)
  (accumulate * 1 term a next b))
