(define (compose f g)
  (lambda (x)
    (f (g x))))

(define (repeated f n)
  (define (iter i repeat-f)
    (if (= i 1)
        repeat-f
        (iter
          (- i 1)
          (compose f repeat-f))))
  (iter n f))

(define (smooth f)
  (define dx 0.00001)
  (lambda (x)
    (/
      (+ (f (- x dx))
         (f x)
         (f (+ x dx)))
      3)))

(define (n-fold-smooth f n)
  ((repeated smooth n) f))
