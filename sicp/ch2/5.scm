(define (pow base exp)
  (define (iter b e result)
    (cond ((= e 0) result)
          ((even? e)
           (iter
             (* b b)
             (/ e 2)
             result))
           (else
             (iter
               b
               (- e 1)
               (* b result)))))
  (iter base exp 1))

(define (mod m)
  (lambda (num)
    (define (iter n result)
      (if (and
            (= (remainder n m) 0)
            (not (= 0 (ceiling (/ n m)))))
          (iter (/ n m) (+ result 1))
          result))
    (iter num 0)))

(define (my-cons a b)
  (if (or (< a 1) (< b 1))
      (error "invalid argument: " a b)
      (* (pow 2 a)
         (pow 3 b))))

(define (my-car p)
  (define mod2 (mod 2))
  (mod2 p))

(define (my-cdr p)
  (define mod3 (mod 3))
  (mod3 p))
