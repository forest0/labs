(define (iterative-improve good-enough? improve)
  (lambda (first-guess)
    (define (iter guess)
      (let ((next (improve guess)))
        (if (good-enough? guess next)
            guess
            (iter next))))
    (iter first-guess)))

(define (square-root x)
  ((iterative-improve
     (lambda (v1 v2)
       (< (abs (- v1 v2))
          0.001))
     (lambda (guess)
       (/ (+ guess (/ x guess))
          2)))
   1.0))

(define (fixed-point f)
  ((iterative-improve
     (lambda (v1 v2)
       (< (abs (- v1 v2))
          0.001))
     (lambda (guess)
       (f guess)))
   1.0))
