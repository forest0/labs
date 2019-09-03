(define f
  (let ((first? #t))
    (lambda (arg)
      (if first?
          (begin (set! first? #f)
                 arg)
          0))))

(define another-f
  (lambda (first-value)
    (set! another-f (lambda (other-value) 0))
    first-value))
