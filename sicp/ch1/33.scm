(define (filtered-accumulate combiner null-value term a next b filter)
  (define (accumulate-iter cur result)
    (cond ((> cur b) result)
          ((filter cur)
           (accumulate-iter
             (next cur)
             (combiner
               (term cur)
               result)))
          (else
            (accumulate-iter
              (next cur)
              result))))
  (accumulate-iter a null-value))

(define (sum-of-square-primes a b)
  (define (prime? n)
    (define (smallest-divisor num)
      (define (iter cur)
        (cond ((> (square cur) num) num)
              ((= 0 (remainder num cur)) cur)
              (else (iter (+ cur 1)))))
      (iter 2))
    (= (smallest-divisor n) n))
  (define (next a)
    (+ a 1))
  (filtered-accumulate + 0 square a next b prime?))

(define (product-of-relative-primes n)
  (define (relative-prime? a)
    (= (gcd a n) 1))
  (define (identity a) a)
  (define (next a) (+ a 1))
  (filtered-accumulate * 1 identity 1 next n relative-prime?))
