(define (compose f g)
  (lambda (x)
    (f (g x))))

(define (repeated-v1 f n)
  (define (iter i repeat-f)
    (if (= i 1)
        repeat-f
        (iter
          (- i 1)
          (lambda (x)
            (f (repeat-f x))))))
  (iter n f))

(define (repeated-v2 f n)
  (define (iter i repeat-f)
    (if (= i 1)
        repeat-f
        (iter
          (- i 1)
          (compose f repeat-f))))
  (iter n f))
